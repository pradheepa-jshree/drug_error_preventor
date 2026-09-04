from pyzbar.pyzbar import decode
from PIL import Image


def decode_barcode(image_path: str) -> list[str]:
    """
    Decode barcodes from an image.

    Returns:
        A list of decoded barcode values.
    """

    image = Image.open(image_path)

    decoded = decode(image)

    barcodes = []

    for barcode in decoded:
        barcode_data = barcode.data.decode("utf-8")

        if barcode_data not in barcodes:
            barcodes.append(barcode_data)

    return barcodes