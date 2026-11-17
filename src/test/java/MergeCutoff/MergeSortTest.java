package MergeCutoff;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.Arrays;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;

class MergeSortTest {

    // 0 random, 1 sorted, 2 reverse, 3 many duplicates, 4 all equal
    private static int[] generate(int n, int type, Random rnd) {
        int[] a = new int[n];
        for (int i = 0; i < n; i++) {
            switch (type) {
                case 0 -> a[i] = rnd.nextInt();
                case 1 -> a[i] = i;
                case 2 -> a[i] = n - i;
                case 3 -> a[i] = rnd.nextInt(5);
                default -> a[i] = 42;
            }
        }
        return a;
    }

    private static void check(int[] input, int cutoff) {
        int[] expected = input.clone();
        Arrays.sort(expected);
        int[] actual = input.clone();
        MergeSort.sort(actual, cutoff);
        assertArrayEquals(expected, actual, "cutoff=" + cutoff + " n=" + input.length);
    }

    @ParameterizedTest
    @ValueSource(ints = {0, 1, 2, 3, 5, 7, 10, 15, 30, 64, 100})
    void smallArraysAllTypes(int cutoff) {
        Random rnd = new Random(12345);
        for (int n = 0; n <= 300; n++) {
            for (int type = 0; type < 5; type++) {
                check(generate(n, type, rnd), cutoff);
            }
        }
    }

    @ParameterizedTest
    @ValueSource(ints = {0, 1, 2, 3, 5, 7, 10, 15, 30, 64, 100})
    void largeRandomArrays(int cutoff) {
        Random rnd = new Random(777);
        check(generate(10_000, 0, rnd), cutoff);
        check(generate(100_000, 0, rnd), cutoff);
    }

    @Test
    void extremeValues() {
        int[] a = {Integer.MAX_VALUE, Integer.MIN_VALUE, 0, -1, 1,
                   Integer.MAX_VALUE, Integer.MIN_VALUE};
        for (int cutoff : new int[]{1, 2, 7, 100}) check(a, cutoff);
    }

    @Test
    void cutoffLargerThanArray() {
        check(new int[]{3, 1, 2}, 1000);   // pure insertion sort path
    }

    @Test
    void emptyAndSingle() {
        check(new int[]{}, 7);
        check(new int[]{5}, 7);
    }
}