import math
import numpy as np
import sys
import random

from datetime import timedelta, datetime


ilosc_wierzcholkow = 20
minimum_krawedzi = 6
maksimum_krawedzi = 30
minimalna_waga = 1
maksymalna_waga = 100

czas_dzialania_algorytmu = 60 * 4 # W sekundach
ilosc_mrowek = 100
ilosc_dopuszczalnych_rozwiazan = 1 # Dla ilu najlepszych rozwiązań zaaktualizować feromony
stopien_parowania_feromonow = 0.1 # Im większy tym bardziej wyparuje, coś pomiędzy 0-1

szansa_uzycia_feromonow = 0.01 # Poczatkowa szansa skorzystania z macierzy feromonów
wzrost_szansy_uzycia_feromonow = 0.001 # Wartość wzrtostu szansy uzycia feromonów

granica_wygladzania = 40 # powyżej tej wartośći feromonu odpali się wygładzanie
wartosc_wygladzania = 20 # im wyższy tym bardziej wygładzi wartości

wartosc_alfa = 1 # wpływ feromonu na prawdopodobieństwo wybrania
wartosc_beta = 0 # wpływ wagi krawędzi na prawdopodobieństwo wybrania

parametr_x = 5



def generuj_losowy_graf():
  graf = np.zeros((ilosc_wierzcholkow, ilosc_wierzcholkow), dtype=int)
  for i in range(1, ilosc_wierzcholkow):
    graf[i-1][i] = graf[i][i-1] = random.randint(minimalna_waga, maksymalna_waga)

  for i in range(ilosc_wierzcholkow):
    do_uzupelnienia = minimum_krawedzi - len(graf[i].nonzero()[0])
    if do_uzupelnienia > 0:
      for _ in range(do_uzupelnienia):
        pozostale = set(range(ilosc_wierzcholkow)) - set(graf[i].nonzero()[0]) - {i}
        while pozostale:
          j = random.choice(tuple(pozostale))
          if len(graf[:,j].nonzero()[0]) < maksimum_krawedzi:
            graf[i][j] = graf[j][i] = random.randint(minimalna_waga, maksymalna_waga)
            break
          pozostale.remove(j)
        else:
          raise Exception('NIE MOŻNA UTWORZYĆ GRAFU')

  assert all(minimum_krawedzi <= len(x.nonzero()[0]) <= maksimum_krawedzi for x in graf)
  return graf


def wylicz_koszt(graf, sciezka):
  wagi = np.empty(sciezka.size - 1, dtype=int)
  for i in range(0, sciezka.size - 1):
    wagi[i] = graf[sciezka[i], sciezka[i + 1]]
    if (i + 1) % parametr_x == 0:
      ile_cofac = math.ceil(parametr_x/2)
      wagi[i] = wagi[i] + 2 * wagi[i+1-ile_cofac:i+1].sum() * len(graf[sciezka[i + 1]].nonzero()[0])
  return wagi.sum()



def start_mrowki(graf, feromony, prawdopodobienstwa):
  # Mrówka porusza się po grafie, szukając sekwencji wierzchołków grafu tworzącej
  # najkrótszą drogę od wierzchołka startowego do końcowego. Pojedyncza mrówka
  # generuje swoją ścieżkę niezależnie od swoich towarzyszek.
  #sciezka = np.empty(ilosc_wierzcholkow, dtype=int)
  sciezka = np.empty(ilosc_wierzcholkow, dtype=int)

  # Dla każdej mrówki generowane jest losowo miasto, z którego ma rozpocząć wędrówkę.
  indeks, maksymalny_indeks = 0, ilosc_wierzcholkow - 1
  sciezka[0] = random.randrange(0, ilosc_wierzcholkow)

  # Rzut losowy na skorzystanie z macierzy feromonów
  uzycie_fermonow = random.random() < szansa_uzycia_feromonow

  # Aby nie wracać do już odwiedzonych wierzchołków, mrówka jest wyposażona w pamięć,
  # w której przechowuje listę takich wierzchołków.
  niedowiedzone = set(range(ilosc_wierzcholkow)) - {sciezka[0]}

  while niedowiedzone: # Dopóki są jeszcze jakieś niedowiedzone
    sasiedzi = graf[sciezka[indeks]].nonzero()[0]

    # Jeżeli istnieją nieodwiedzeni sąsiedzi to zawsze wybieramy któryś z nich
    niedowiedzeni_sasiedzi = tuple(niedowiedzone & set(sasiedzi))
    #if niedowiedzeni_sasiedzi and not uzycie_fermonow:
    if niedowiedzeni_sasiedzi:
      if uzycie_fermonow:
        # Kopiujemy prawdopodobieństwa tylko nieodwiedzonych wierzchołków
        prawdopodobienstwa_niedowiedzonych = np.zeros(ilosc_wierzcholkow)
        prawdopodobienstwa_niedowiedzonych[niedowiedzeni_sasiedzi, ] = \
          prawdopodobienstwa[sciezka[indeks], niedowiedzeni_sasiedzi]

        # Losujemy nieodwiedzony wierzchołek na podstawie ich prawdopodobieństw
        nastepny = random.choices(list(range(0, ilosc_wierzcholkow)),
                                  weights=prawdopodobienstwa_niedowiedzonych)[0]
      else:
        # Losujemy nieodwiedzony wierzchołek z równymi szansami
        nastepny = random.choice(niedowiedzeni_sasiedzi)
    else:
      if uzycie_fermonow:
        # Losujemy jakikolwiek sąsiedni wierzchołek na podstawie prawdopodobieństw
        nastepny = random.choices(list(range(0, ilosc_wierzcholkow)),
                          weights=prawdopodobienstwa[sciezka[indeks]])[0]
      else:
        # Losujemy jakikolwiek sąsiedni wierzchołek z równymi szansami
        nastepny = random.choice(sasiedzi)

    if nastepny in niedowiedzone:
      niedowiedzone.remove(nastepny)
    indeks += 1
    if indeks > maksymalny_indeks:
      sciezka.resize(maksymalny_indeks + 11)
      maksymalny_indeks += 10
    sciezka[indeks] = nastepny



  sciezka.resize(indeks + 1)
  return wylicz_koszt(graf, sciezka), sciezka



if __name__ == "__main__":
  # Tworzymy trzy macierze:
  # 1. Macierz grafu na połączenia, jeżeli nie ma połączenia pomiędzy wierzchołkami
  #    to w polu jest 0, jeżeli połączenie istnieje to w polu jest waga krawędzi
  #    wybrana losowo pomiędzy minimalna_waga i maksymalna_waga. Np:
  # [[ 0 62 87 90  0  0 22 15 92  0]
  #  [62  0 98 18 58  0  0 55 19 95]
  #  [87 98  0 34 80 77 15 12 41 35]
  #  [90 18 34  0 22 88  0 55  0 65]
  #  [ 0 58 80 22  0 64 55  0 91  0]
  #  [ 0  0 77 88 64  0  5  0 72 48]
  #  [22  0 15  0 55  5  0 65 23 44]
  #  [15 55 12 55  0  0 65  0 64  0]
  #  [92 19 41  0 91 72 23 64  0 83]
  #  [ 0 95 35 65  0 48 44  0 83  0]]
  macierz_grafu = generuj_losowy_graf()

  # 2. Macierz feromonów, wypełniamy ją 1 wszędzie tam gdzie istnieje połączenie
  #    pomiędzy wierzchołkami.
  # [[0. 1. 1. 1. 0. 0. 1. 1. 1. 0.]
  #  [1. 0. 1. 1. 1. 0. 0. 1. 1. 1.]
  #  [1. 1. 0. 1. 1. 1. 1. 1. 1. 1.]
  #  [1. 1. 1. 0. 1. 1. 0. 1. 0. 1.]
  #  [0. 1. 1. 1. 0. 1. 1. 0. 1. 0.]
  #  [0. 0. 1. 1. 1. 0. 1. 0. 1. 1.]
  #  [1. 0. 1. 0. 1. 1. 0. 1. 1. 1.]
  #  [1. 1. 1. 1. 0. 0. 1. 0. 1. 0.]
  #  [1. 1. 1. 0. 1. 1. 1. 1. 0. 1.]
  #  [0. 1. 1. 1. 0. 1. 1. 0. 1. 0.]]
  macierz_feromonow = np.zeros((ilosc_wierzcholkow, ilosc_wierzcholkow), dtype=float)
  macierz_feromonow[macierz_grafu.nonzero()] = 1


  # 3. Macierz prawdopodobieństwa
  macierz_prawdopodobienstwa = np.zeros((ilosc_wierzcholkow, ilosc_wierzcholkow), dtype=float)
  macierz_prawdopodobienstwa = np.copy(macierz_feromonow)
  

  #print(macierz_grafu)
  #print(macierz_feromonow)
  #print(macierz_prawdopodobienstwa)


  najlepsze_rozwiazanie = None
  stop = datetime.now() + timedelta(seconds=czas_dzialania_algorytmu)
  while datetime.now() < stop:
    sciezki = []
    for _ in range(ilosc_mrowek):
      sciezki.append(start_mrowki(macierz_grafu,
                                  macierz_feromonow,
                                  macierz_prawdopodobienstwa))

    sciezki = sorted(sciezki, key=lambda x: x[0]) # Sortujemy sciezki po koszcie
    najlepsze_sciezki = sciezki[:ilosc_dopuszczalnych_rozwiazan]


    # Aktualizacja feromonów, dodajemy wartości pomiędzy 0.1-1
    # 1 dla najlepszej ścieżki, 0.1 dla najgorszej
    roznica = najlepsze_sciezki[-1][0] - najlepsze_sciezki[0][0]
    for koszt, sciezka in najlepsze_sciezki:
      if roznica:
        moc_feromonu = (koszt - najlepsze_sciezki[0][0]) / roznica * 0.9
      else:
        moc_feromonu = 1

      for j in range(0, len(sciezka) - 1):
        k, l = sciezka[j:j+2]
        macierz_feromonow[k, l] += 1 - moc_feromonu


    # Parowanie feromonów
    macierz_feromonow *= 1 - stopien_parowania_feromonow


    # Aktualizacja prawdopodobieństw
    macierz_prawdopodobienstwa = (macierz_feromonow ** wartosc_alfa)
    macierz_prawdopodobienstwa *= (macierz_grafu / 1) ** wartosc_beta


    # Wygładzanie
    for wiersz in macierz_feromonow:
      if np.where(wiersz > granica_wygladzania)[0].size:
        minimum = wiersz[wiersz.nonzero()].min()
        for i, x in enumerate(wiersz):
          if x > 0:
            wiersz[i] = minimum * (1 + math.log(x / minimum, wartosc_wygladzania))


    szansa_uzycia_feromonow += wzrost_szansy_uzycia_feromonow

    if not najlepsze_rozwiazanie or sciezki[0][0] < najlepsze_rozwiazanie:
      najlepsze_rozwiazanie = sciezki[0][0]
      print(najlepsze_rozwiazanie)