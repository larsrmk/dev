'''mermaid
flowchart TD
    subgraph Sender
        N1[Klartext-Nachricht] --> H1(Hash-Funktion)
        H1 --> F1[Fingerabdruck / Hash]
        F1 -->|Verschlüsselt mit Private Key| S[Digitale Signatur]
        N1 --> Output
        S --> Output[Nachricht + Signatur]
    end

    subgraph Übertragung
        Output -->|Internet| Input[Empfangene Daten]
    end

    subgraph Empfänger
        Input --> N2[Empfangene Nachricht]
        Input --> S2[Empfangene Signatur]
        
        N2 --> H2(Hash-Funktion)
        H2 --> F2[Neuer Fingerabdruck]
        
        S2 -->|Entschlüsselt mit Public Key \n aus dem Zertifikat| F3[Entschlüsselter Fingerabdruck]
        
        F2 ---|Vergleich: Stimmen überein?| F3
    end
    
    CA((Zertifizierungsstelle)) -.->|Bestätigt Identität des Public Keys| S2

'''