package MergeCutoff;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public class Benchmark {
    static final int[] CUTOFFS = buildCutoffs();
    static final int WARMUP_ROUNDS = 5;   // full passes over all cutoffs, discarded

    static int[] buildCutoffs() {
        int[] extra = {40, 50, 64, 100};
        int[] c = new int[30 + extra.length];
        for (int i = 0; i < 30; i++) c[i] = i + 1;
        System.arraycopy(extra, 0, c, 30, extra.length);
        return c;
    }

    static int trialsFor(int n) {
        if (n <= 10_000) return 50;
        if (n <= 100_000) return 30;
        return 20;
    }

    public static void main(String[] args) throws IOException {
        Path dataDir = Paths.get(args.length > 0 ? args[0] : "data");
        Path out = Paths.get(args.length > 1 ? args[1] : "results/raw.csv");
        int trialsOverride = args.length > 2 ? Integer.parseInt(args[2]) : -1;
        Files.createDirectories(out.toAbsolutePath().getParent());

        Random order = new Random(42);
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(out))) {
            w.println("size,input_type,cutoff,trial,time_ns");

            for (int n : DataGenerator.SIZES) {
                for (String type : DataGenerator.TYPES) {
                    int[] data = DataGenerator.read(dataDir.resolve(type + "_" + n + ".bin"));
                    int[] work = new int[n];
                    int trials = trialsOverride > 0 ? trialsOverride : trialsFor(n);
                    System.out.printf("size=%d type=%s trials=%d%n", n, type, trials);

                    // warm-up: results discarded
                    for (int r = 0; r < WARMUP_ROUNDS; r++) {
                        for (int cutoff : CUTOFFS) {
                            System.arraycopy(data, 0, work, 0, n);
                            MergeSort.sort(work, cutoff);
                        }
                    }

                    // measured trials: cutoff order shuffled in every trial
                    List<Integer> cutoffOrder = new ArrayList<>();
                    for (int c : CUTOFFS) cutoffOrder.add(c);

                    int sink = 0;  // keeps the JIT from discarding the work
                    for (int t = 1; t <= trials; t++) {
                        Collections.shuffle(cutoffOrder, order);
                        for (int cutoff : cutoffOrder) {
                            System.arraycopy(data, 0, work, 0, n);   // outside the timed region
                            long start = System.nanoTime();
                            MergeSort.sort(work, cutoff);
                            long elapsed = System.nanoTime() - start;
                            sink += work[n / 2];
                            w.println(n + "," + type + "," + cutoff + "," + t + "," + elapsed);
                        }
                    }
                    if (sink == 42) System.out.println();   // use sink
                    w.flush();
                }
            }
        }
        System.out.println("Done: " + out.toAbsolutePath());
    }
}
