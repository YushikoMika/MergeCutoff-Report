package MergeCutoff;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Random;

public class DataGenerator {
    static final long SEED = 20261114L;
    static final int[] SIZES = {10_000, 100_000, 1_000_000};
    static final String[] TYPES = {"random", "sorted", "reverse", "nearly_sorted", "duplicates"};

    public static void main(String[] args) throws IOException {
        Path dir = Paths.get(args.length > 0 ? args[0] : "data");
        Files.createDirectories(dir);
        for (int n : SIZES) {
            for (String type : TYPES) {
                Random rnd = new Random(SEED + n + type.hashCode());
                write(dir.resolve(type + "_" + n + ".bin"), generate(n, type, rnd));
            }
        }
        System.out.println("Datasets written to " + dir.toAbsolutePath());
    }

    public static int[] generate(int n, String type, Random rnd) {
        int[] a = new int[n];
        switch (type) {
            case "random" -> { for (int i = 0; i < n; i++) a[i] = rnd.nextInt(); }
            case "sorted" -> { for (int i = 0; i < n; i++) a[i] = i; }
            case "reverse" -> { for (int i = 0; i < n; i++) a[i] = n - i; }
            case "nearly_sorted" -> {
                for (int i = 0; i < n; i++) a[i] = i;
                for (int s = 0; s < n / 100; s++) {      // swap ~1% random pairs
                    int i = rnd.nextInt(n), j = rnd.nextInt(n);
                    int t = a[i]; a[i] = a[j]; a[j] = t;
                }
            }
            case "duplicates" -> { for (int i = 0; i < n; i++) a[i] = rnd.nextInt(100); }
            default -> throw new IllegalArgumentException(type);
        }
        return a;
    }

    public static void write(Path p, int[] a) throws IOException {
        ByteBuffer buf = ByteBuffer.allocate(a.length * 4);
        buf.asIntBuffer().put(a);
        Files.write(p, buf.array());
    }

    public static int[] read(Path p) throws IOException {
        byte[] bytes = Files.readAllBytes(p);
        int[] a = new int[bytes.length / 4];
        ByteBuffer.wrap(bytes).asIntBuffer().get(a);
        return a;
    }
}
