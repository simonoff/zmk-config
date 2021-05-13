CHAR_MAP = {
    "`": "GRAVE",
    "~": "LS(GRAVE)",
    "!": "LS(1)",
    "@": "LS(2)",
    "#": "LS(3)",
    "$": "LS(4)",
    "%": "LS(5)",
    "^": "LS(6)",
    "&": "LS(7)",
    "\*": "LS(8)",
    "(": "LS(9)",
    ")": "LS(0)",
    "-": "MINUS",
    "_": "LS(MINUS)",
    "=": "EQUAL",
    "+": "LS(EQUAL)",
    "[": "LBKT",
    "{": "LS(LBKT)",
    "]": "RBKT",
    "}": "LS(RBKT)",
    "\\": "BSLH",
    "\|": "LS(BSLH)",
    ";": "SEMI",
    ":": "LS(SEMI)",
    "'": "SQT",
    '"': "LS(SQT)",
    ",": "COMMA",
    "<": "LS(COMMA)",
    ".": "DOT",
    ">": "LS(DOT)",
    "/": "FSLH",
    "?": "LS(FSLH)",
}


def map_char(character):
    character = character.upper()
    if character.isalpha():
        return character
    if character.isdigit():
        return f"N{character}"
    elif character in CHAR_MAP:
        return CHAR_MAP[character]
    return None


def custom_key_behavior(name, key0, key1):
    return f"""
        {name}: {name} {{
            compatible = "zmk,behavior-mod-morph";
            label = "Generated Behavior {name}";
            #binding-cells = <0>;
            bindings = <&kp {key0}>, <&kp {key1}>;
            mods = <(MOD_LGUI|MOD_LSFT|MOD_RGUI|MOD_RSFT)>;
        }};
    """


LAYERS = {"lwr": 1, "rse": 2, "adj": 3}

MODIFIERS = {
    "alt": "LALT",
    "shft": "LSHFT",
    "cmd": "LGUI",
    "ctrl": "LCTRL",
}

class MarkdownLayer(object):
    "Parses markdown tables into a list of labels for each keyboard row."
    @classmethod
    def parse(cls, source_lines):
        layers = []
        table = None
        for line in source_lines:
            line = line.strip()
            if table is not None:
                if line.startswith("|"):
                    table.append([col.strip() for col in line.split("|")])
                else:
                    layers.append(cls(table))
                    table = None
            elif line.startswith("| -"):
                table = []
        if table is not None:
            layers.append(cls(table))
        return layers

    def __init__(self, markdown_table):
        self.main_rows = []
        for row in markdown_table[:3]:
            self.main_rows.append(row[1:6] + row[7:12])

        hold_row = markdown_table[3]
        tap_row = markdown_table[4]
        combined_row = list(zip(hold_row, tap_row))
        self.thumb_row = combined_row[3:6] + combined_row[7:10]


class DtsiKeymap(object):
    "Converts a list of MarkdownLayers into a dtsi keymap file."
    def __init__(self, markdown_layers):
        self.behaviors = []
        self.layers = []
        for layer in markdown_layers:
            self.add_layer(layer)

    def add_layer(self, markdown_layer: MarkdownLayer):
        layer = []
        for row in markdown_layer.main_rows:
            layer.append(
                "&trans " + " ".join(self.map_label(label) for label in row) + " &trans"
            )
        layer.append(
            " ".join(
                self.map_thumb_key(hold, tap) for hold, tap in markdown_layer.thumb_row
            )
        )
        self.layers.append("\n".join(layer))

    def map_space_separated_label(self, label):
        parts = label.split(" ")
        if len(parts) != 2:
            return None
        behavior_name = f"custom{len(self.behaviors)}"
        self.behaviors.append(
            custom_key_behavior(behavior_name, map_char(parts[0]), map_char(parts[1]))
        )
        return f"&{behavior_name}"

    def map_simple_label(self, label):
        char = map_char(label)
        if char:
            return f"&kp {char}"
        return None

    def map_label(self, label):
        if not label:
            zmk = "&trans"
        elif label.startswith("&") and len(label) > 1:
            zmk = label
        elif " " in label:
            zmk = self.map_space_separated_label(label)
        else:
            zmk = self.map_simple_label(label)

        if zmk is None:
            print("unknown key label:", label)
            return "&trans"
        return zmk

    def map_thumb_key(self, hold, tap):
        tap_char = map_char(tap)
        if hold in LAYERS:
            if tap_char:
                return f"&lt_ {LAYERS[hold]} {tap_char}"
            else:
                return f"&mo {LAYERS[hold]}"
        elif hold in MODIFIERS:
            if tap_char:
                return f"&mt_ {MODIFIERS[hold]} {map_char(tap)}"
            else:
                return f"&kp {MODIFIERS[hold]}"
        return "&trans"

    def generate_dtsi(self, template_path):
        with open(template_path, "r") as template_file:
            template = template_file.read()
            template = template.replace("#BEHAVIORS#", "".join(self.behaviors))
            for i, layer in enumerate(self.layers):
                template = template.replace(f"#LAYER_{i}#", layer)
            return template


with open("keymap.md", "r") as source:
    markdown_layers = MarkdownLayer.parse(source.readlines())
    keymap = DtsiKeymap(markdown_layers)
    dtsi = keymap.generate_dtsi("keymap_template.dtsi")
    open("config/corne.keymap", "w").write(dtsi)
