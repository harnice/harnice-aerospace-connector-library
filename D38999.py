import re


def find_mating_connector(
    part_number,
    override_shell_style = None,
    override_finish = None,
    override_insert_arrangement = None,
    override_gender = None,
    override_keyway = None,
    return_divider = None
    ):
    """
    Given a MIL-DTL-38999 part number, returns the mating connector part number
    as a string in D38999_ format.

    Supports a number of prefixes.
    Supports Series I, II, III, and IV style codes.

    D38999 Series III part number structure (after the style code):
      [Shell Style 1] [Contact Style 1] [Insert Arrangement 2-3] [Shell Material 1] [Key 1]
      e.g. /26 F G16 S N
            ^  ^  ^^ ^ ^
            |  |  |  | └─ Master keyway arrangement
            |  |  |  └─── Pins or Sockets
            |  |  └────── Insert arrangement (2-3 digits)
            |  └───────── Finish
            └──────────── Shell style

    Args:
      part_number:                      The MIL-DTL-38999 part number string.
      override_shell_style:             Assert a shell style. 
      override_finish:                  Assert a finish.
      override_insert_arrangement:      Assert an insert arrangement.
      override_gender:                  Assert pins/sockets.
      override_keyway:                  Assert a master keyway.
      return_divider:                   By default, Harnice will return an underscore D38999_xxxxxx. You can change that here. 

    Returns:
      Mating part number string in D38999_ format.
    """

    mating_shell_styles = {  # given a shell size in the input, what shell size should be returned
        # Series I
        "01": "13",
        "03": "15",
        "05": "17",
        "13": "01",
        "15": "03",
        "17": "05",
        # Series II
        "11": "33",
        "33": "11",
        # Series III
        "20": "26",
        "24": "26",
        "26": "24",
        # Series IV
        "41": "53",
        "43": "55",
        "53": "41",
        "55": "43",
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

    valid_genders = {"P": "S", "S": "P"}

    # Normalize - accept various input formats
    pn = (
        part_number.strip().upper().replace(" ", "")
    )  # force input to caps, remove spaces
    pn = pn.replace("_", "/").replace("-", "/") # allow underscore or dash in leading name
    pn = pn.replace("MS38999", "D38999")  # allow MS38999
    pn = pn.replace("MIL-DTL-38999", "D38999") # allow MIL-DTL-38999

    match = re.match(r"^D38999/(\d{2})([A-Z])([A-Z])(\d{1,2})([A-Z])([A-Z])$", pn)
    if not match:
        raise ValueError(
            f"Could not parse '{part_number}' as a MIL-DTL-38999 part number. "
            "Expected format: D38999/XX[shell_style][contact][insert][material][key] "
            "(e.g. D38999/26FG16SN)."
        )

    shell_style = match.group(1)  # e.g. "26"
    finish = match.group(2)  # e.g. "F"
    shell_size = match.group(3)  # e.g. "G" (gender: A=pin, B=socket... or other)
    insert_arrangement_suffix = match.group(4)  # e.g. "16"
    insert_arrangement = f"{shell_size}{insert_arrangement_suffix}"
    gender = match.group(5)  # e.g. "S"
    key = match.group(6)  # e.g. "N"

    if shell_style not in mating_shell_styles:
        raise ValueError(
            f"Unknown shell style '{shell_style}'. "
            f"Supported shell styles: {sorted(mating_shell_styles.keys())}"
        )
    mating_shell_style = mating_shell_styles.get(shell_style)
    if override_shell_style:
        mating_shell_style = override_shell_style

    # Preserve finish
    if finish not in valid_finishes:
        raise ValueError(
            f"Unknown shell style '{shell_style}'. "
            f"Supported shell styles: {sorted(mating_shell_styles.keys())}"
        )
    mating_finish = finish
    if override_finish:
        mating_finish = override_finish

    # Preserve insert arrangement
    mating_insert_arrangement = insert_arrangement
    if override_insert_arrangement:
        mating_insert_arrangement = override_insert_arrangement

    # Flip contact gender
    if gender not in valid_genders:
        raise ValueError(
            f"Unknown gender '{shell_style}'. "
            f"Supported genders: {sorted(mating_shell_styles.keys())}"
        )
    mating_gender = valid_genders.get(gender)
    if override_gender:
        mating_gender = override_gender

    # Preserve key
    mating_key = key
    if override_keyway:
        mating_key = override_keyway

    if return_divider:
        divider = return_divider
    else:
        divider = "_"

    return f"D38999{divider}{mating_shell_style}{mating_finish}{mating_insert_arrangement}{mating_gender}{mating_key}"
