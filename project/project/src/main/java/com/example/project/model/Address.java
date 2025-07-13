package com.example.project.model;

import jakarta.persistence.Embeddable;

@Embeddable
public class Address {

    private String streetAndNumber;  // Straße und Hausnummer zusammen
    private String postalCode;
    private String city;

    // Standardkonstruktor (wichtig für JPA)
    public Address() {}

    // Konstruktor zum einfachen Erstellen
    public Address(String streetAndNumber, String postalCode, String city) {
        this.streetAndNumber = streetAndNumber;
        this.postalCode = postalCode;
        this.city = city;
    }

    // Getter und Setter
    public String getStreetAndNumber() {
        return streetAndNumber;
    }

    public void setStreetAndNumber(String streetAndNumber) {
        this.streetAndNumber = streetAndNumber;
    }

    public String getPostalCode() {
        return postalCode;
    }

    public void setPostalCode(String postalCode) {
        this.postalCode = postalCode;
    }

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }
}