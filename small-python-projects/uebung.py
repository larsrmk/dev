class Frage:
    def __init__(self, text, antworten, antwort_richtig):
        self.text = text
        self.antworten = antworten
        self.antwort_richtig = antwort_richtig

    def pruefe_antwort(self, benutzer_antwort):
        return benutzer_antwort.lower() == self.antwort_richtig.lower()


def quiz_spiel(fragen):
    punkte = 0

    for i, frage in enumerate(fragen, 1):
        print(f"\nFrage {i}: {frage.text}")

        for j, antwort in enumerate(frage.antworten, 1):
            print(f"{chr(96 + j)}) {antwort}")

        benutzer_antwort = input("Ihre Antwort (a/b/c/d): ").lower() 

        if frage.pruefe_antwort(benutzer_antwort):
            print("Richtig! Sie erhalten einen Punkt.")
            punkte += 1
        else:
            print(f"Falsch! Die richtige Antwort ist {frage.antwort_richtig}.")

    print(f"\nQuiz beendet! Sie haben {punkte} von {len(fragen)} Punkten erreicht.")

if __name__ == "__main__":
    frage1 = Frage("Wie viele Planeten gibt es in unserem Sonnensystem?",
                   ["a) Sechs", "b) Acht", "c) Neun", "d) Zwölf"],
                   "b")

    frage2 = Frage("Woran erkennt man den Unterschied zwischen der Flagge Rumäniens und der Flagge von Tschad?",
                   ["a) An den Seitenverhältnissen", "b) An den Farben", "c) An der Anordnung der Farben", "d) Am Blauton des blauen Streifens"],
                   "d")

    frage3 = Frage("Wie lautet die Hauptstadt von Japan?",
                   ["a) Peking", "b) Bangkok", "c) Seoul", "d) Tokio"],
                   "d")

    frage4 = Frage("Was ist die Hauptkomponente der Luft?",
                   ["a) Sauerstoff", "b) Stickstoff", "c) Kohlendioxid", "d) Wasserstoff"],
                   "b")

    frage5 = Frage("in welchem Jahr wurde JFK ermordet?",
                   ["a) 1963", "b) 1783", "c) 1863", "d) 1964"],
                   "a")

    fragen = [frage1, frage2, frage3, frage4, frage5]

    quiz_spiel(fragen)


