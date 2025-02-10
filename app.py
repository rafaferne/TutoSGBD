import tkinter as tk
import pyodbc
from datetime import datetime

# Base de datos
def conectar_bd():
    try:
        conexion = pyodbc.connect(
            "DSN=seminario1;"
            "UID=x8110538;"
            "PWD=x8110538;"
        )
        return conexion
    except pyodbc.Error as e:
        print("Error al conectar a la base de datos:", e)
        return None

# Mostrar tablas
def mostrar_contenido_bd():
    conexion = conectar_bd()
    if conexion:
        cursor = conexion.cursor()
        try:
            print("\nContenido de la tabla Stock:")
            cursor.execute("SELECT * FROM Stock")
            for row in cursor.fetchall():
                print(row)

            print("\nContenido de la tabla Pedido:")
            cursor.execute("SELECT * FROM Pedido")
            for row in cursor.fetchall():
                print(row)

            print("\nContenido de la tabla Detalle_Pedido:")
            cursor.execute("SELECT * FROM Detalle_Pedido")
            for row in cursor.fetchall():
                print(row)
        except Exception as e:
            print(f"Error al mostrar contenido de la base de datos: {e}")
        finally:
            cursor.close()
            conexion.close()

# Creacion de tablas
def crear_tablas():
    conexion = conectar_bd()
    if conexion:
        cursor = conexion.cursor()
        try:
            # Borrar las tablas si existen
            try:
                cursor.execute("DROP TABLE Detalle_Pedido")
            except:
                pass
            try:
                cursor.execute("DROP TABLE Pedido")
            except:
                pass
            try:
                cursor.execute("DROP TABLE Stock")
            except:
                pass

            # Crear las tablas de nuevo
            cursor.execute("""
                CREATE TABLE Stock (
                    CProducto NUMBER PRIMARY KEY,
                    Cantidad NUMBER
                )
            """)

            cursor.execute("""
                CREATE TABLE Pedido (
                    CPedido NUMBER PRIMARY KEY,
                    CCliente NUMBER,
                    FechaPedido DATE
                )
            """)

            cursor.execute("""
                CREATE TABLE Detalle_Pedido (
                    ID NUMBER PRIMARY KEY,
                    CoPedido NUMBER,
                    CoProducto NUMBER,
                    Cantidad NUMBER,
                    FOREIGN KEY (CoProducto) REFERENCES Stock(CProducto),
                    FOREIGN KEY (CoPedido) REFERENCES Pedido(CPedido)
                )
            """)

            # Tuplas predefinidas
            productos = [(1, 100), (2, 200), (3, 50), (4, 300), (5, 150), (6, 250), (7, 30), (8, 180), (9, 120), (10, 80)]

            cursor.executemany("""
                INSERT INTO Stock (CProducto, Cantidad)
                VALUES (?, ?)
            """, productos)

            conexion.commit()
            print("Tablas recreadas y tuplas insertadas con éxito.")
            mostrar_contenido_bd()
        
        except Exception as e:
            print(f"Error al ejecutar la acción: {e}")
        
        finally:
            cursor.close()
            conexion.close()

# Función para abrir una nueva alta
def dar_nueva_alta():
    ventana_nueva = tk.Toplevel(ventana)
    ventana_nueva.title("Dar de alta nuevo pedido")
    ventana_nueva.geometry("300x400")

    # Crear conexión a la base de datos una sola vez para toda la sesión
    conexion = conectar_bd()
    cursor = conexion.cursor() if conexion else None

    #Creacion de campos a rellenar
    tk.Label(ventana_nueva, text="ID Pedido").pack()
    entry_cpedido = tk.Entry(ventana_nueva)
    entry_cpedido.pack(pady=5)

    tk.Label(ventana_nueva, text="ID Cliente").pack()
    entry_ccliente = tk.Entry(ventana_nueva)
    entry_ccliente.pack(pady=5)

    tk.Label(ventana_nueva, text="Fecha Pedido (YYYY-MM-DD)").pack()
    entry_fecha_pedido = tk.Entry(ventana_nueva)
    entry_fecha_pedido.pack(pady=5)

    def insertar_pedido():
        cpedido = entry_cpedido.get()
        ccliente = entry_ccliente.get()
        fecha_pedido = entry_fecha_pedido.get()

        if cursor:
            try:
                cursor.execute("""
                    INSERT INTO Pedido (CPedido, CCliente, FechaPedido)
                    VALUES (?, ?, ?)
                """, (int(cpedido), int(ccliente), datetime.strptime(fecha_pedido, '%Y-%m-%d').date()))
                conexion.commit()
                print("Pedido insertado con éxito.")
                mostrar_contenido_bd()
            except Exception as e:
                print(f"Error al insertar pedido: {e}")

    # Botón insertar
    boton_insertar = tk.Button(ventana_nueva, text="Insertar Pedido", command=insertar_pedido)
    boton_insertar.pack(pady=10)

    # Botón detalle producto
    def abrir_detalle_producto():
        ventana_detalle = tk.Toplevel(ventana_nueva)
        ventana_detalle.title("Añadir detalle de producto")
        ventana_detalle.geometry("300x200")

        tk.Label(ventana_detalle, text="ID Pedido").pack()
        entry_co_pedido = tk.Entry(ventana_detalle)
        entry_co_pedido.pack(pady=5)

        tk.Label(ventana_detalle, text="ID Producto").pack()
        entry_co_producto = tk.Entry(ventana_detalle)
        entry_co_producto.pack(pady=5)

        tk.Label(ventana_detalle, text="Cantidad").pack()
        entry_cantidad = tk.Entry(ventana_detalle)
        entry_cantidad.pack(pady=5)

        def insertar_detalle():
            co_pedido = int(entry_co_pedido.get())
            co_producto = int(entry_co_producto.get())
            cantidad = int(entry_cantidad.get())

            if cursor:
                try:
                    # Creamos savepoints
                    cursor.execute("SAVEPOINT DetalleProducto")
                    cursor.execute("""
                        INSERT INTO Detalle_Pedido (ID, CoPedido, CoProducto, Cantidad)
                        VALUES ((SELECT COALESCE(MAX(ID), 0) + 1 FROM Detalle_Pedido), ?, ?, ?)
                    """, (co_pedido, co_producto, cantidad))
                    
                    cursor.execute("UPDATE Stock SET Cantidad = Cantidad - ? WHERE CProducto = ?", (cantidad, co_producto))
                    conexion.commit()
                    print("Detalle de producto añadido y stock actualizado.")
                    mostrar_contenido_bd()
                except Exception as e:
                    # Rollback si ocurre un error
                    cursor.execute("ROLLBACK TO SAVEPOINT DetalleProducto")
                    print(f"Error al insertar detalle o actualizar stock, operación revertida: {e}")

        boton_insertar_detalle = tk.Button(ventana_detalle, text="Insertar Detalle", command=insertar_detalle)
        boton_insertar_detalle.pack(pady=10)

    boton_añadir_detalle = tk.Button(ventana_nueva, text="Añadir detalle de producto", command=abrir_detalle_producto)
    boton_añadir_detalle.pack(pady=10)
    
    # Botón eliminar detalles del pedido
    def eliminar_detalles_pedido():
        cpedido = entry_cpedido.get()

        if cursor:
            try:
                # Creamos savepoints
                cursor.execute("SAVEPOINT EliminarDetalles")
                
                # Obtener los detalles del pedido para restaurar stock
                cursor.execute("SELECT CoProducto, Cantidad FROM Detalle_Pedido WHERE CoPedido = ?", (int(cpedido),))
                detalles = cursor.fetchall()
                
                for co_producto, cantidad in detalles:
                    cursor.execute("UPDATE Stock SET Cantidad = Cantidad + ? WHERE CProducto = ?", (cantidad, co_producto))
                
                cursor.execute("DELETE FROM Detalle_Pedido WHERE CoPedido = ?", (int(cpedido),))
                conexion.commit()
                print("Detalles del pedido eliminados y stock restaurado.")
                mostrar_contenido_bd()

            except Exception as e:
                cursor.execute("ROLLBACK TO SAVEPOINT EliminarDetalles")
                print(f"Error al eliminar detalles del pedido: {e}")

    boton_eliminar_detalles = tk.Button(ventana_nueva, text="Eliminar todos los detalles del producto", command=eliminar_detalles_pedido)
    boton_eliminar_detalles.pack(pady=10)

    # Botón eliminar el pedido y sus detalles
    def eliminar_detalles_producto_pedido():
        cpedido = entry_cpedido.get()
        
        if cursor:
            try:
                cursor.execute("SAVEPOINT CancelarPedido")
                
                # Obtener los detalles del pedido para restaurar el stock
                cursor.execute("SELECT CoProducto, Cantidad FROM Detalle_Pedido WHERE CoPedido = ?", (int(cpedido),))
                detalles = cursor.fetchall()
                
                for co_producto, cantidad in detalles:
                    cursor.execute("UPDATE Stock SET Cantidad = Cantidad + ? WHERE CProducto = ?", (cantidad, co_producto))
                
                cursor.execute("DELETE FROM Detalle_Pedido WHERE CoPedido = ?", (int(cpedido),))
                cursor.execute("DELETE FROM Pedido WHERE CPedido = ?", (int(cpedido),))
                conexion.commit()
                print("Pedido y sus detalles eliminados, y stock restaurado.")
                mostrar_contenido_bd()
                
            except Exception as e:
                cursor.execute("ROLLBACK TO SAVEPOINT CancelarPedido")
                print(f"Error al cancelar el pedido y restaurar el stock: {e}")

    boton_eliminar_detalles_producto = tk.Button(ventana_nueva, text="Cancelar pedido", command=eliminar_detalles_producto_pedido)
    boton_eliminar_detalles_producto.pack(pady=10)
    
    # Botón finalizar el pedido y guardar todos los cambios
    def finalizar_pedido():
        if conexion:
            try:
                conexion.commit()  # Confirmar todos los cambios realizados
                print("Cambios confirmados en la base de datos.")
                mostrar_contenido_bd()
            except Exception as e:
                print(f"Error al confirmar los cambios: {e}")
            finally:
                cursor.close()
                conexion.close()
            ventana_nueva.destroy()

    boton_finalizar_pedido = tk.Button(ventana_nueva, text="Finalizar pedido", command=finalizar_pedido)
    boton_finalizar_pedido.pack(pady=10)


# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Gestión de Pedidos")
ventana.geometry("400x300")

# Crear los botones del menú principal
boton1 = tk.Button(ventana, text="Borrar y crear tablas", command=crear_tablas)
boton1.pack(pady=5)

boton2 = tk.Button(ventana, text="Dar de alta nuevo pedido", command=dar_nueva_alta)
boton2.pack(pady=5)

# Botón para mostrar el contenido de la base de datos
boton3 = tk.Button(ventana, text="Mostrar contenido de la BD", command=mostrar_contenido_bd)
boton3.pack(pady=5)

boton_salir = tk.Button(ventana, text="Salir", command=ventana.destroy)
boton_salir.pack(pady=5)

# Iniciar el loop de la ventana
ventana.mainloop()
