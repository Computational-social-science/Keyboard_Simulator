MANUAL_LAYOUT = [
    {
        "key_id": "key_esc",
        "label": "esc",
        "type": "special_control",
        "group": "function_keys",
        "font_color": "#888888",
        "background_color": "#1C1C1E",
        "position": {'x': 50, 'y': 16, 'width': 74, 'height': 74},
        "characters": ["escape"]
    },
    {
        "key_id": "key_f1",
        "label": "F1",
        "type": "function",
        "group": "function_keys",
        "font_color": "#888888",
        "background_color": "#1C1C1E",
        "position": {'x': 131, 'y': 16, 'width': 74, 'height': 74},
        "characters": ["f1"]
    },
    {
        "key_id": "key_grave",
        "label": "~", # The instruction uses "~", but often this key shows ` or ~ with shift.
                      # The characters list ["`", "~"] is more accurate.
                      # For label, usually the unshifted character or a symbol representing both is shown.
                      # Sticking to "~" as per instruction for label.
        "type": "number_main",
        "group": "main_keys", # Assuming this is part of main key block, not function keys
        "font_color": "#FFFFFF",
        "background_color": "#1C1C1E",
        "position": {'x': 50, 'y': 107, 'width': 82, 'height': 82},
        "characters": ["`", "~"]
    },
    {
        "key_id": "key_q",
        "label": "Q",
        "type": "alpha",
        "group": "main_keys",
        "font_color": "#FFFFFF",
        "background_color": "#1C1C1E",
        "position": {'x': 180, 'y': 196, 'width': 82, 'height': 82},
        "characters": ["q", "Q"]
    },
    {
        "key_id": "key_a",
        "label": "A",
        "type": "alpha",
        "group": "main_keys",
        "font_color": "#FFFFFF",
        "background_color": "#1C1C1E",
        "position": {'x': 201, 'y': 285, 'width': 82, 'height': 82},
        "characters": ["a", "A"]
    },
    {
        "key_id": "key_shift_left",
        "label": "Shift",
        "type": "modifier",
        "group": "main_keys",
        "font_color": "#888888",
        "background_color": "#1C1C1E",
        "position": {'x': 50, 'y': 374, 'width': 185, 'height': 82},
        "characters": ["shift"]
    },
    {
        "key_id": "key_space",
        "label": "Space",
        "type": "special_control",
        "group": "main_keys",
        "font_color": "#FFFFFF",
        "background_color": "#1C1C1E",
        "position": {'x': 441, 'y': 463, 'width': 513, 'height': 82},
        "characters": [" "]
    }
]

if __name__ == '__main__':
    # Helper to print out the layout for verification
    import json
    print(json.dumps(MANUAL_LAYOUT, indent=4))

    # Verification of calculations (matches the thought process)
    # Esc Key: x=50, y=16
    # F1 Key: x=50+74+7 = 131, y=16
    # Grave/Tilde Key: y_pos_num_row = 16+74+17 = 107. x=50, y=107
    # Q Key: y_pos_q_row = 107 + 82 + 7 = 196. x_pos_q = 50 + 123 + 7 = 180. x=180, y=196
    # A Key: y_pos_a_row = 196 + 82 + 7 = 285. x_pos_a = 50 + 144 + 7 = 201. x=201, y=285
    # Left Shift Key: y_pos_shift_row = 285 + 82 + 7 = 374. x=50, y=374
    # Space Key: y_pos_space_row = 374 + 82 + 7 = 463. x_pos_space = 50 + 103+7 + 123+7 + 144+7 = 441. x=441, y=463

    # Corrected A key y_pos:
    # y_pos_a_row = 16 (Y_offset) + 74 (key_height_func) + 17 (f_row_to_main_row_gap) + (82 (key_height_alpha) + 7 (spacing_px)) * 2
    #             = 16 + 74 + 17 + (89 * 2)
    #             = 107 + 178 = 285. This is correct.

    # Corrected Q key y_pos:
    # y_pos_q_row = 16 (Y_offset) + 74 (key_height_func) + 17 (f_row_to_main_row_gap) + (82 (key_height_alpha) + 7 (spacing_px)) * 1
    #             = 107 + 89 = 196. This is correct.
    
    # Corrected Grave key y_pos:
    # y_pos_num_row = 16 (Y_offset) + 74 (key_height_func) + 17 (f_row_to_main_row_gap)
    #                 = 107. This is correct.
    
    # Notes on group for Grave key:
    # The instruction says "type: number_main (as it's on the number row)".
    # Typically, the number row (1-0, grave, -, =) is considered part of the main key block.
    # So, `group: "main_keys"` seems appropriate. I've used that.
    # If it was intended to be `group: "function_keys"`, that would be unusual.
    pass
