#include <stdio.h>
#include <time.h>
#include <windows.h>
#include "model.h"

int main(void) {
    float in[MODEL_INPUT_DIM] = {0.0f};
    float out[MODEL_OUTPUT_DIM];

    LARGE_INTEGER freq, start, end;
    QueryPerformanceFrequency(&freq);

    /* Warm-up */
    for (int i = 0; i < 100; i++) {
        model_predict(in, out);
    }

    const int iterations = 10000;
    QueryPerformanceCounter(&start);
    for (int i = 0; i < iterations; i++) {
        model_predict(in, out);
    }
    QueryPerformanceCounter(&end);

    double elapsed_sec = (double)(end.QuadPart - start.QuadPart) / (double)freq.QuadPart;
    double avg_us = (elapsed_sec / iterations) * 1e6;
    double avg_ms = avg_us / 1000.0;
    printf("Total time for %d calls: %.4f seconds\n", iterations, elapsed_sec);
    printf("Average inference latency: %.3f us (%.3f ms)\n", avg_us, avg_ms);
    return 0;
}
