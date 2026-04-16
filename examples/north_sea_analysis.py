"""North Sea analysis and plotting example for pymizer."""

from pathlib import Path

import matplotlib.pyplot as plt
import pymizer as mz


def main() -> None:
    north_sea = mz.load_north_sea()
    sim = north_sea.params.project(
        t_max=2,
        dt=0.1,
        t_save=1,
        effort=0,
        progress_bar=False,
    )

    biomass = sim.biomass()
    pred_mort = sim.pred_mort()
    large_fish = sim.proportion_of_large_fish()

    biomass_long = biomass.reset_index().melt(id_vars="time", var_name="species", value_name="biomass")

    print(biomass.iloc[:2, :3])
    print(biomass_long.head())
    print(large_fish.head())
    print(pred_mort.sel(sp="Cod").isel(time=0).to_pandas().head())

    out_dir = Path("examples/output")
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4))
    biomass[["Cod", "Haddock", "Herring"]].plot(ax=ax)
    ax.set_ylabel("Biomass")
    ax.set_title("North Sea Biomass Through Time")
    fig.tight_layout()
    fig.savefig(out_dir / "north_sea_biomass.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    pred_mort.sel(sp="Cod").isel(time=0).plot(ax=ax)
    ax.set_title("Cod Predation Mortality At First Saved Time")
    fig.tight_layout()
    fig.savefig(out_dir / "north_sea_cod_pred_mort.png", dpi=150)
    plt.close(fig)

    print(f"Saved plots to {out_dir}")


if __name__ == "__main__":
    main()
