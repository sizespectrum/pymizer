"""Minimal end-to-end example for pymizer."""

import pymizer as mz


def main() -> None:
    params = mz.new_community_params(no_w=20)
    sim = params.project(t_max=5, dt=0.1, t_save=1, progress_bar=False)
    print(sim.times())
    print(sim.biomass())


if __name__ == "__main__":
    main()
