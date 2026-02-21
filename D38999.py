import re

def find_mating_connector(part_number: str, override_finish: str = None) -> str:
    """
    Given a MIL-DTL-38999 part number, returns the mating connector part number
    as a string in D38999_ format.

    Supports prefixes: M38999/, MS38999/, D38999/, D38999_
    Supports Series I, II, III, and IV style codes.

    D38999 Series III part number structure (after the style code):
      [Shell Style 1] [Contact Style 1] [Insert Arrangement 2-3] [Shell Material 1] [Key 1]
      e.g. /26 F G 16 S N
                ^  ^  ^^ ^ ^
                |  |  |  | └─ Key/finish (preserved or overridden)
                |  |  |  └─── Shell material
                |  |  └────── Insert arrangement (2-3 digits)
                |  └───────── Contact style / gender (A=pin, B=socket)
                └──────────── Shell style

    Args:
      part_number:     The MIL-DTL-38999 part number string.
      override_finish: Optional 1-letter key/finish code to apply to the mating
                       connector instead of preserving the input's key.

    Returns:
      Mating part number string in D38999_ format.
    """

    series_mating = {
        # Series I
        "01": "13", "03": "15", "05": "17",
        "13": "01", "15": "03", "17": "05",
        # Series II
        "11": "33", "33": "11",
        # Series III
        "20": "26", "24": "26",
        "26": "24",
        # Series IV
        "41": "53", "43": "55",
        "53": "41", "55": "43",
    }

    valid_finishes = {
        "A": "Cadmium olive drab",
        "B": "Cadmium clear/bright",
        "C": "Zinc-nickel olive drab",
        "D": "Electroless nickel",
        "E": "Anodized (aluminum)",
        "F": "Black anodized (aluminum)",
        "G": "Nickel PTFE",
        "H": "Hard anodized",
        "N": "Electroless nickel",
        "S": "Stainless passivated",
        "W": "Nickel",
        "Y": "Cadmium yellow chromate",
        "Z": "Zinc-nickel black",
    }

    # Normalize
    pn = part_number.strip().upper().replace(" ", "").replace("-", "")
    pn = re.sub(r'^MS38999', 'M38999', pn)
    pn = re.sub(r'^D38999[/_]', 'M38999/', pn)
    pn = re.sub(r'^D38999', 'M38999', pn)

    match = re.match(r'^M38999/(\d{2})([A-Z])([A-Z])(\d{2,3})([A-Z])([A-Z])$', pn)
    if not match:
        raise ValueError(
            f"Could not parse '{part_number}' as a MIL-DTL-38999 part number. "
            "Expected format: M38999/XX[shell_style][contact][insert][material][key] "
            "(e.g. M38999/26FG16SN)."
        )

    suffix        = match.group(1)  # e.g. "26"
    shell_style   = match.group(2)  # e.g. "F"
    contact       = match.group(3)  # e.g. "G" (gender: A=pin, B=socket... or other)
    insert        = match.group(4)  # e.g. "16"
    material      = match.group(5)  # e.g. "S"
    key           = match.group(6)  # e.g. "N"

    if suffix not in series_mating:
        raise ValueError(
            f"Unknown series/style suffix '{suffix}'. "
            f"Supported suffixes: {sorted(series_mating.keys())}"
        )

    # Flip contact gender
    gender_flip = {"A": "B", "B": "A"}
    mating_contact = gender_flip.get(contact, contact)

    mating_key = key

    # Apply finish/material override if provided
    mating_material = material
    if override_finish is not None:
        override_finish = override_finish.strip().upper()
        if override_finish not in valid_finishes:
            raise ValueError(
                f"Unknown finish code '{override_finish}'. "
                f"Valid codes: {sorted(valid_finishes.keys())}"
            )
        mating_material = override_finish

    mating_suffix = series_mating[suffix]
    return f"D38999_{mating_suffix}{shell_style}{mating_contact}{insert}{mating_material}{mating_key}"


# ── Example usage ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        ("D38999/26FG16SN",  None),    # your test case
        ("M38999/20WA35SN",  None),
        ("D38999/22WA9PN",   None),
        ("D38999_28WB9PN",   None),
        ("D38999/20WA35SN",  "W"),     # finish override
    ]

    for pn, finish in tests:
        result = find_mating_connector(pn, override_finish=finish)
        print(f"Input:  {pn}")
        print(f"Mating: {result}")
        print()