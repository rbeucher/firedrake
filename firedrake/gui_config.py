"""A GUI for setting parameters"""

from __future__ import absolute_import

from Tkinter import *
from ttk import *

__all__ = ['show_config_gui']


def show_config_gui(parameters):
    from firedrake import Parameters

    if not isinstance(parameters, Parameters):
        raise TypeError("Expected Type: Parameters")

    def load_json():
        import tkFileDialog
        filename = tkFileDialog.askopenfilename()
        import_params_from_json(parameters, filename)
        refresh_params(parameters, variable_dict)

    def save_json():
        import tkFileDialog
        if save_params():
            filename = tkFileDialog.asksaveasfilename()
            export_params_to_json(parameters, filename)

    def save_and_quit():
        if save_params():
            root.destroy()

    def save_params():
        try:
            parsed_dict = parse_input_dict(parameters, variable_dict)
            load_from_dict(parameters, parsed_dict)
            return True
        except ValueError as e:
            from tkMessageBox import showinfo
            showinfo(title="Error", message=e.message, icon="error", parent=root)
            return False

    def refresh_params(parameters, variable_dict):
        for key in parameters.keys():
            if isinstance(parameters[key], Parameters):
                refresh_params(parameters[key], variable_dict[key])
            else:
                variable_dict[key].set(str(parameters[key]))

    def parse_input_dict(parameters, variable_dict):
        from firedrake import Parameters

        parsed_dict = {}
        for key in variable_dict.keys():
            if isinstance(parameters[key], Parameters):
                parsed_dict[key] = parse_input_dict(parameters[key],
                                                    variable_dict[key])
            else:
                str_val = variable_dict[key].get()
                if not parameters.get_key(key).validate(str_val):
                    raise ValueError("Invalid value for parameter %s" % key)
                parsed_dict[key] = parameters.get_key(key).type.parse(str_val)
        return parsed_dict

    def generate_input(parameters, labelframe, variable_dict):
        global row_count
        keys = sorted(parameters.keys())
        for key in keys:
            row_count += 1
            if isinstance(parameters[key], Parameters):
                subframe = Labelframe(labelframe, text=key, padding='3 3 12 12')
                subframe.grid(column=1, columnspan=4, row=row_count, sticky=(W, E))
                subframe.columnconfigure(1, weight=1)
                subframe.rowconfigure(0, weight=1)
                variable_dict[key] = {}
                generate_input(parameters[key], subframe, variable_dict[key])
            else:
                label_key = Label(labelframe, text=key)
                label_key.grid(column=1, row=row_count, sticky=(W))
                variable_dict[key] = StringVar()
                variable_dict[key].set(str(parameters[key]))
                if type(parameters[key]) is not bool:
                    if type(parameters[key]) is str and \
                            parameters.get_key(key).type.options != []:
                        drop_list = OptionMenu(labelframe, variable_dict[key],
                                               parameters[key],
                                               *parameters.get_key(key).type.options)
                        drop_list.grid(column=2, columnspan=2, row=row_count, sticky=(E))
                    else:
                        label_val = Entry(labelframe, textvariable=variable_dict[key])
                        label_val.grid(column=2, columnspan=2, row=row_count, sticky=(E))
                else:
                    button_true = Radiobutton(labelframe, text='True',
                                              variable=variable_dict[key],
                                              value="True")
                    button_true.grid(column=2, row=row_count, sticky=(E))
                    button_false = Radiobutton(labelframe, text='False',
                                               variable=variable_dict[key],
                                               value="False")
                    button_false.grid(column=3, row=row_count, sticky=(E))

                def help_box(key):
                    def click():
                        from tkMessageBox import showinfo
                        showinfo(title="Help", message=key.help, parent=root)
                    return click

                help_button = Button(labelframe, text='Help',
                                     command=help_box(parameters.get_key(key)))
                help_button.grid(column=4, row=row_count, sticky=(E))

    def configure_frame(event):
        size = (mainframe.winfo_reqwidth(), mainframe.winfo_reqheight())
        canvas.config(scrollregion="0 0 %s %s" % size)
        if mainframe.winfo_reqwidth() != canvas.winfo_width():
            canvas.config(width=mainframe.winfo_reqwidth())

    def configure_canvas(event):
        if mainframe.winfo_reqwidth() != canvas.winfo_width():
            canvas.itemconfigure(frame_id, width=canvas.winfo_width())

    global root
    root = Tk()
    root.title("Configure")

    canvas = Canvas(root, borderwidth=0)

    mainframe = Frame(canvas, padding='3 3 12 12')
    mainframe.grid(row=0, column=0, sticky=(N, W, E, S))
    mainframe.columnconfigure(0, weight=1)
    mainframe.rowconfigure(0, weight=1)

    scrollbar = Scrollbar(root, orient=VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    frame_id = canvas.create_window(0, 0, window=mainframe, anchor=NW)

    global row_count
    row_count = 1

    variable_dict = {}
    generate_input(parameters, mainframe, variable_dict)

    row_count += 1
    button_load = Button(mainframe,
                         text="Load from File",
                         command=load_json)
    button_load.grid(column=1, row=row_count, sticky=W)
    button_save = Button(mainframe, text="Save to File", command=save_json)
    button_save.grid(column=3, row=row_count, sticky=S)
    button_quit = Button(mainframe, text="Save and Quit", command=save_and_quit)
    button_quit.grid(column=4, row=row_count, sticky=E)

    mainframe.bind('<Configure>', configure_frame)
    canvas.bind('<Configure>', configure_canvas)

    root.mainloop()


def export_params_to_json(parameters, filename):
    import json

    if filename == '':
        return
    output_file = open(filename, 'w')
    output_file.write(json.dumps(parameters))
    output_file.close()


def import_params_from_json(parameters, filename):
    import json

    if filename == '':
        return
    input_file = open(filename, 'r')
    dictionary = json.loads(input_file.read())
    input_file.close()
    load_from_dict(parameters, dictionary)
    return parameters


def load_from_dict(parameters, dictionary):
    from firedrake import Parameters
    from firedrake.logging import warning

    for k in dictionary:
        if k in parameters:
            if isinstance(parameters[k], Parameters):
                load_from_dict(parameters[k], dictionary[k])
            else:
                try:
                    if isinstance(dictionary[k], unicode):
                        # change unicode type to str type
                        parameters[k] = dictionary[k].encode('ascii', 'ignore')
                    else:
                        parameters[k] = dictionary[k]
                except ValueError as e:
                    from tkMessageBox import showinfo
                    showinfo(title="Error", message=e.message, icon="error", parent=root)
        else:
            warning(k + ' is not in the parameters and ignored')
