import argparse

import qrcode
from qrcode.image.svg import SvgPathImage as Factory
from yaml import safe_load


def create_qr_code(data: str, box_size: int = 10, border: int = 4) -> tuple[bytes, int]:
    """
    The version parameter is an integer from 1 to 40 that controls the size of the QR Code (the smallest, version 1, is a 21x21 matrix). Set to None and use the fit parameter when making the code to determine this automatically.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white", image_factory=Factory)
    size = (qr.modules_count + 2 * border) * box_size
    return img.to_string(), size


def create_qr_grid(
    data_list: list[str],
    grid_size: tuple[int, int],
    qr_size: int = 100,
    spacing: int = 10,
    output_file: str = "output.svg",
    max_size: int | None = None,
):
    cols, rows = grid_size

    svg_header = f'<svg xmlns="http://www.w3.org/2000/svg" width="{cols * (qr_size + spacing)}" height="{rows * (qr_size + spacing)}">'
    svg_footer = "</svg>"
    svg_content = [svg_header]

    max_size_ = 0
    qrcodes = []
    sizes = []

    for d in data_list:
        qr_svg, size = create_qr_code(d, box_size=4, border=0)
        qrcodes.append(qr_svg)
        sizes.append(size)
        max_size_ = max(max_size_, size)

    if max_size is None:
        max_size = max_size_

    scaling_factors = [max_size / size for size in sizes]

    for i, data in enumerate(qrcodes):
        row = i // cols
        col = i % cols

        x = col * (qr_size + spacing)
        y = row * (qr_size + spacing)

        scale = scaling_factors[i]
        qr_svg = data

        qr_svg_transformed = (
            f'<g transform="translate({x},{y}) scale({scale})">{qr_svg}</g>'
        )
        svg_content.append(qr_svg_transformed)

    svg_content.append(svg_footer)
    with open(output_file, "w") as f:
        f.write("\n".join(svg_content))


def main():
    parser = argparse.ArgumentParser(
        description="Generate QR codes based on a list of objects in a yaml file"
    )
    parser.add_argument("--conf", type=str, help="YAML configuration file")
    parser.add_argument(
        "--output", type=str, help="Output file name", default="output.svg"
    )
    parser.add_argument(
        "--what",
        type=str,
        help="What to generate [C]onstellations ,[O]bjects, [S]cripts",
        default="COS",
    )
    args = parser.parse_args()

    with open(args.conf, "r") as file:
        conf = safe_load(file)

        data = []
        if "C" in args.what:
            constellations = conf["constellations"].keys()
            data.extend(list(constellations))
        if "O" in args.what:
            objects = conf["objects"]
            data.extend(objects)
        if "S" in args.what:
            direct_scripts = [
                k
                for k in conf["scripts"].keys()
                if k not in ["constellation", "object"]
            ]
            data.extend(direct_scripts)

        if "C" in args.what:
            constellations = conf["constellations"].keys()
            data = list(constellations)

    grid_size = (8, 11)
    create_qr_grid(data, grid_size, qr_size=90, spacing=10, max_size=200)


if __name__ == "__main__":
    main()
