"""EP 09 elif, BLACK GRID version: same video as build_ep09.py, only the background is swapped
for the animated black grid (brand/dark_grid.py)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "brand"))
import build_ep09 as m        # noqa: E402
import dark_grid as dg        # noqa: E402

m.e.board_bg = lambda: dg.background(m.p7._T[0])
m.e.OUT = os.path.join(HERE, "output", "Python_ki_Pathshala_EP09_Elif_BlackGrid.mp4")

if __name__ == "__main__":
    m.e.main()
