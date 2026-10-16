"""EP 08 if-else, BLACK GRID version: same video as build_ep08.py, only the background is swapped
for the animated black grid (brand/dark_grid.py)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ep08 as m        # noqa: E402
import dark_grid as dg        # noqa: E402  (brand/ is on sys.path via build_ep08)

m.background = dg.background
m.OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP08_IfElse_BlackGrid.mp4")

if __name__ == "__main__":
    m.main()
