package com.example;

public class SampleClass {
    private String cached;

    public int add(int a, int b) { return a + b; }

    public String concat(String a, String b) { return a + b; }

    private boolean hidden(int x) { return x > 0; }
}
