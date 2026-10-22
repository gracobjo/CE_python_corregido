import tkinter as tk
from PIL import Image, ImageTk


ventana = tk.Tk()
ventana.title("Aplicación con imagen")
ventana.geometry("500x350")
ventana.iconbitmap(r"C:\Users\PHY\Documents\CE_Python-1\Imagenes\python.ico")

ruta_imagen = r"C:\Users\PHY\Documents\CE_Python-1\Imagenes\python.png"
imagen = Image.open(ruta_imagen)
imagen = imagen.resize((120, 120))
imagen_tk = ImageTk.PhotoImage(imagen)

label_imagen = tk.Label(ventana, image=imagen_tk)
label_imagen.pack(pady=10)

etiqueta = tk.Label(ventana, text="Etiqueta antes de pulsar el botón", font=("Arial", 14))
etiqueta.pack(pady=10)

boton = tk.Button(
    ventana,
    text="Haz clic aquí",
    command=lambda: etiqueta.config(text="Has hecho clic en el botón."),
    bg="lightblue",
)
boton.pack(pady=10)

ventana.mainloop()