"""North Sea example workflow for pymizer."""

import pymizer as mz


def main() -> None:
    north_sea = mz.load_north_sea()

    print(north_sea.species_params.head(2))
    print(north_sea.interaction.iloc[:2, :2])
    print(north_sea.params.biomass().head())

    sim = north_sea.params.project(
        t_max=1,
        dt=0.1,
        t_save=1,
        effort=0,
        progress_bar=False,
    )
    print(sim.biomass().iloc[:2, :3])


if __name__ == "__main__":
    main()
