import sys

def expected_gcd(gcd, fps):
    return gcd + ((1 - gcd * fps) % 1) * (1 / fps)

def max_diff(gcd_a, gcd_b, min_fps = 21, max_fps = 121):
    best_diff = 0
    best_fps = 0

    for fps in range(min_fps, max_fps):
        exp_a = expected_gcd(gcd_a, fps)
        exp_b = expected_gcd(gcd_b, fps)
        diff = abs(exp_a - exp_b)

        if diff > best_diff:
            best_diff = diff
            best_fps = fps

    return best_diff, best_fps

def cum_diff(gcd_a, gcd_b, min_fps = 21, max_fps = 121):
    pass  # TODO

if __name__ == "__main__":
    gcd_a = float(sys.argv[1])
    gcd_b = float(sys.argv[2])

    print(f'Testing {gcd_a} vs {gcd_b}..')

    best_diff, best_fps = max_diff(gcd_a, gcd_b)

    print(f'Biggest predicted GCD disparity ({best_diff}) found at {best_fps} fps')