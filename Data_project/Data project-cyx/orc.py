from fontTools.ttLib import TTFont
import os

def get_fingerprint(font, glyph_name):
    """
    Generates a binary grid string (fingerprint) for a given glyph
    based on its coordinates.
    """
    try:
        glyph = font['glyf'][glyph_name]
        coordinates = glyph.getCoordinates(font['glyf'])[0]

        xs = [p[0] for p in coordinates]
        ys = [p[1] for p in coordinates]
        if not xs or not ys: return None

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max_x - min_x
        height = max_y - min_y

        if width == 0 or height == 0: return None

        # 10x10 Grid
        grid_size = 10
        grid = [['0'] * grid_size for _ in range(grid_size)]

        for x, y in zip(xs, ys):
            # Normalize
            gx = int((x - min_x) / width * (grid_size - 1))
            # Flip Y-axis
            gy = int((1 - (y - min_y) / height) * (grid_size - 1))

            if 0 <= gx < grid_size and 0 <= gy < grid_size:
                grid[gy][gx] = '1'

        return "".join(["".join(row) for row in grid])

    except Exception as e:
        return None


def main():
    font_path = 'base_font.woff'
    if not os.path.exists(font_path):
        print("base_font.woff not found.")
        return

    font = TTFont(font_path)
    print("Scanning font file...")

    # Find all 'uni' glyphs
    uni_glyphs = [name for name in font.getGlyphOrder() if name.startswith('uni')]

    print("input the digit (0-9) for each glyph code.")


    results = {}

    for name in uni_glyphs:
        fp = get_fingerprint(font, name)
        if fp:
            val = input(f"Glyph {name} corresponds to digit? (0-9, Enter to skip): ")
            if val.strip():
                results[val.strip()] = fp

    print("self.standard_fingerprints = {")
    for k, v in sorted(results.items()):
        print(f"    '{k}': '{v}',")
    print("}")


if __name__ == "__main__":
    main()