import csv
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import threading
import time
import serial.tools.list_ports


class DataCollectorApp:
    def __init__(self, root):
        self.root = root
        root.configure(bg='black')
        self.root.title("Curve Catcher")

        # Configurar estilo do gráfico
        self.fig, self.ax = plt.subplots()
        self.fig.patch.set_facecolor('black')
        self.ax.set_facecolor('black')  # Fundo preto
        self.ax.grid(True, color='gray', linestyle='--', linewidth=0.5)  # Grade cinza claro

        self.line, = self.ax.plot([], [], color='lime', marker='o', linestyle='-', markersize=5)  # Linha verde com pontos
        self.ax.set_title("Curva Característica do Diodo", fontsize=12, color='white')
        self.ax.set_xlabel("Tensão (V)", fontsize=12, color='white')
        self.ax.set_ylabel("Corrente (mA)", fontsize=12, color='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')

        # Ajustar limites dos eixos
        self.ax.set_xlim(0, 5)  # Exemplo de limites para a tensão
        #self.ax.set_ylim(0, 25)  # Exemplo de limites para a corrente

        # Adicionar a legenda
        self.ax.legend(['Curva I-V'], loc='upper right', fontsize=10, facecolor='black', edgecolor='white', labelcolor='white')

        # Canvas para mostrar o gráfico na interface
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Frame para os controles
        control_frame = tk.Frame(root, bg="black")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
       
        # Dropdown 
        self.port_var = tk.StringVar()
        self.port_menu = ttk.Combobox(control_frame, textvariable=self.port_var, state='readonly', width=20)
        self.update_ports()
        self.port_menu.grid(row=0, column=0, padx=5, pady=5)

        # Botão para conectar
        self.connect_button = ttk.Button(control_frame, text="Connect", command=self.connect_to_port)
        self.connect_button.grid(row=0, column=1, padx=5, pady=5)

        # Área para exibir o status da conexão
        self.status_label = tk.Label(control_frame, text="Not connected", fg="red")
        self.status_label.grid(row=0, column=2, padx=5, pady=5)

        # Sliders para ajustar os limites dos eixos
        self.x_min_lim_slider = tk.Scale(control_frame, from_=-10, to=10, resolution=0.1, orient=tk.HORIZONTAL, label="Tensão Mín", bg='black', fg='white')
        self.x_min_lim_slider.set(0)
        self.x_min_lim_slider.grid(row=1, column=1, padx=5, pady=5)
        self.x_min_lim_slider.bind("<B1-Motion>", self.update_axes)  # Atualiza o gráfico em tempo real
        self.x_min_lim_slider.bind("<Double-1>", self.on_double_click)

        self.y_min_lim_slider = tk.Scale(control_frame, from_=-50, to=50, resolution=0.1, orient=tk.HORIZONTAL, label="Corrente Mín", bg='black', fg='white')
        self.y_min_lim_slider.set(0)
        self.y_min_lim_slider.grid(row=1, column=2, padx=5, pady=5)
        self.y_min_lim_slider.bind("<B1-Motion>", self.update_axes)  # Atualiza o gráfico em tempo real
        self.y_min_lim_slider.bind("<Double-1>", self.on_double_click)

        self.x_max_lim_slider = tk.Scale(control_frame, from_=-10, to=10, resolution=0.1, orient=tk.HORIZONTAL, label="Tensão Máx", bg='black', fg='white')
        self.x_max_lim_slider.set(5)
        self.x_max_lim_slider.grid(row=1, column=3, padx=5, pady=5)
        self.x_max_lim_slider.bind("<B1-Motion>", self.update_axes)  # Atualiza o gráfico em tempo real
        self.x_max_lim_slider.bind("<Double-1>", self.on_double_click)

        self.y_max_lim_slider = tk.Scale(control_frame, from_=-50, to=50, resolution=0.1, orient=tk.HORIZONTAL, label="Corrente Máx", bg='black', fg='white')
        self.y_max_lim_slider.set(50)
        self.y_max_lim_slider.grid(row=1, column=4, padx=5, pady=5)
        self.y_max_lim_slider.bind("<B1-Motion>", self.update_axes)  # Atualiza o gráfico em tempo real
        self.y_max_lim_slider.bind("<Double-1>", self.on_double_click)

        # Botões
        self.start_button = ttk.Button(control_frame, text="Iniciar Coleta", command=self.start_data_collection)
        self.start_button.grid(row=0, column=3, padx=5, pady=5)

        self.clear_button = ttk.Button(control_frame, text="Limpar Gráfico", command=self.clear_plot)
        self.clear_button.grid(row=0, column=4, padx=5, pady=5)

        # Botão para salvar os dados
        self.save_button = ttk.Button(control_frame, text="Salvar", command=self.save_data_and_plot)
        self.save_button.grid(row=0, column=5, padx=5, pady=5)

        # Botão de Sair
        self.exit_button = ttk.Button(control_frame, text="Sair", command=self.root.quit)  # Fecha a janela
        self.exit_button.grid(row=0, column=6, padx=5, pady=5)


        self.data = []
        self.collecting = False
        self.serial_port = self.port_var.get()  # Porta serial a ser usada 
        
    def on_double_click(self, event):
        slider = event.widget

        # Criar uma nova janela para a entrada do valor
        value_window = tk.Toplevel(self.root)
        value_window.title("Valor")
        value_window.geometry("200x100")

        value_label = ttk.Label(value_window, text="Digite um valor:")
        value_label.pack(pady=10)

        value_entry = tk.Entry(value_window)
        value_entry.pack(pady=5)

        def set_value():
            try:
                value = float(value_entry.get())
                slider.set(value)
                value_window.destroy()  # Fechar a janela após definir o valor
            except ValueError:
                pass  # Ignorar se o valor não for um número válido

        set_button = ttk.Button(value_window, text="Set", command=set_value)
        set_button.pack(pady=5)


    def update_axes(self, event=None):
        try:
            x_min = float(self.x_min_lim_slider.get())
            x_max = float(self.x_max_lim_slider.get())
            y_min = float(self.y_min_lim_slider.get())
            y_max = float(self.y_max_lim_slider.get())
            self.ax.set_xlim(x_min, x_max)
            self.ax.set_ylim(y_min, y_max)
            self.canvas.draw()
        except ValueError:
            tk.messagebox.showerror("Erro", "Por favor, insira valores numéricos válidos.")

    def start_data_collection(self):
        if not self.collecting:
            self.collecting = True
            self.data = []  # Reiniciar dados
            threading.Thread(target=self.collect_data).start()

    def collect_data(self):
        try:
            with serial.Serial(self.serial_port, 9600, timeout=1) as ser:
                for _ in range(50):  # Ajuste o número de leituras conforme necessário
                    if not self.collecting:
                        break
                    line = ser.readline().decode().strip()  # Leitura da linha da porta serial
                    if line:
                        try:
                            corrente, tensao = map(float, line.split(","))
                            self.data.append((tensao, corrente))
                            self.update_plot()
                        except ValueError:
                            continue  # Ignorar linhas inválidas
                    time.sleep(0.1)
        except serial.SerialException as e:
            print(f"Erro de comunicação com a porta serial: {e}")
            messagebox.showerror("Erro de comunicação com a porta serial:", str(e))
            self.status_label.config(text="Erro de Comunicação", fg="red")
        finally:
            self.collecting = False

    def update_plot(self):
        tensoes, correntes = zip(*self.data) if self.data else ([], [])
        self.line.set_data(tensoes, correntes)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def clear_plot(self):
        if not self.collecting:
            self.data = []
            self.line.set_data([], [])
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
        else: print("we are still collecting!")

    def update_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_menu['values'] = [port.device for port in ports]
        self.port_menu.current(0) if ports else self.port_menu.set("No ports available")

    def connect_to_port(self):
        selected_port = self.port_var.get()
        try:
            self.serial_connection = serial.Serial(selected_port, 9600, timeout=1)
            self.status_label.config(text=f"Connected to {selected_port}", fg="green")
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", str(e))
            self.status_label.config(text="Not connected", fg="red")

    def save_data_and_plot(self):
        if self.data:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                     filetypes=[("CSV files", "*.csv"),
                                                                ("All files", "*.*")])
            if file_path:
                # Salvar os dados em um arquivo CSV
                with open(file_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Tensão (V)", "Corrente (mA)"])
                    writer.writerows(self.data)
                print(f"Dados salvos em {file_path}")
                # Salvar o gráfico em uma imagem
                plot_file_path = file_path.replace('.csv', '.png')
                self.fig.savefig(plot_file_path)
                print(f"Gráfico salvo em {plot_file_path}")
        else:
            print("Nenhum dado para salvar.")
            messagebox.showerror("Erro", "Nenhum dado para salvar")

if __name__ == "__main__":
    root = tk.Tk()
    app = DataCollectorApp(root)
    root.mainloop()
