import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error
from tkinter import ttk

class DatabaseHandler:
    def __init__(self):
        self.logged_in = False
        self.mydb = None
        self.mycursor = None

    def connect(self):
        try:
            self.mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",  
                database="shoesport"
            )
            self.mycursor = self.mydb.cursor(buffered=True)
            self.logged_in = True
        except Error as err:
            messagebox.showerror("Erreur", f"Erreur lors de la connexion à la base de données : {err}")
            self.mycursor = None
            self.mydb = None
            self.logged_in = False

    def close_connection(self):
        if self.mycursor:
            self.mycursor.close()
        if self.mydb:
            self.mydb.close()
        self.logged_in = False

    def verify_admin(self, username, motdepasse):
        try:
            self.connect()
            if self.mycursor:
                query = "SELECT * FROM admin WHERE username = %s AND motdepasse = %s"
                self.mycursor.execute(query, (username, motdepasse))
                result = self.mycursor.fetchone()
                self.close_connection()
                return result is not None
            else:
                return False
        except Error as err:
            messagebox.showerror("Erreur", f"Erreur lors de la vérification de l'administrateur : {err}")
            self.close_connection()
            return False

class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Service client")
        self.root.configure(bg="white")
        self.db_handler = DatabaseHandler()
        self.etat_probleme_var = tk.StringVar()
        self.radio_buttons = {}
        self.state_entries = {}

        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack(expand=True, fill="both")

        self.frames = {}
        self.create_frames()
        self.show_frame("Connexion")

    def create_frames(self):
        self.frames["Connexion"] = tk.Frame(self.main_frame, bg="white")
        self.create_connexion_frame(self.frames["Connexion"])

        self.frames["Main"] = tk.Frame(self.main_frame, bg="white")
        self.create_main_frame(self.frames["Main"])

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.pack(expand=True, fill="both")
        frame.tkraise()

    def hide_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.pack_forget()

    def create_connexion_frame(self, parent_frame):
        frame_connexion = tk.Frame(parent_frame, bg="white", borderwidth=5, relief=tk.RIDGE, highlightbackground="white")
        frame_connexion.pack(expand=True, padx=20, pady=20)

        label_username = tk.Label(frame_connexion, text="Nom d'utilisateur:", bg='white', font=("Arial", 12))
        label_username.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.entry_username = tk.Entry(frame_connexion, width=20, bg='white', font=("Arial", 12))
        self.entry_username.grid(row=0, column=1, padx=5, pady=5)

        label_password = tk.Label(frame_connexion, text="Mot de passe:", bg='white', font=("Arial", 12))
        label_password.grid(row=1, column=0, padx=5, pady=5, sticky="e")

        self.entry_password = tk.Entry(frame_connexion, show="*", width=20, bg='white', font=("Arial", 12))
        self.entry_password.grid(row=1, column=1, padx=5, pady=5)

        bouton_connexion = tk.Button(frame_connexion, text="Se connecter", command=self.valider_connexion, width=20, height=2, bg="white", borderwidth=2, relief=tk.GROOVE, font=("Arial", 12))
        bouton_connexion.grid(row=2, columnspan=2, padx=5, pady=15)

    def create_main_frame(self, parent_frame):
        self.canvas = tk.Canvas(parent_frame, bg="white")
        self.canvas.pack(side="left", expand=True, fill="both")

        self.scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.message_frame = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0, 0), window=self.message_frame, anchor='nw')

        self.canvas.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        bouton_deconnexion = tk.Button(parent_frame, text="Se déconnecter", command=self.deconnexion, width=20, height=2, bg="white", borderwidth=2, relief=tk.GROOVE, font=("Arial", 12))
        bouton_deconnexion.pack(side="bottom", pady=10)

    def valider_connexion(self):
        username = self.entry_username.get()
        motdepasse = self.entry_password.get()

        if self.db_handler.verify_admin(username, motdepasse):
            self.db_handler.connect()
            if self.db_handler.logged_in:
                self.hide_frame("Connexion")
                self.show_frame("Main")
                self.afficher_infosclient_et_messages()
                self.afficher_infos_utilisateurs()
                self.afficher_infos_produits()
                self.afficher_infos_pointure()
            else:
                messagebox.showerror("Erreur", "Impossible de se connecter à la base de données.")
        else:
            messagebox.showerror("Erreur", "Nom d'utilisateur ou mot de passe incorrect")

    def deconnexion(self):
        self.db_handler.close_connection()
        self.hide_frame("Main")
        self.show_frame("Connexion")

    def envoyer_reponse(self, message_id, entry_reponse):
        reponse = entry_reponse.get()
        etat_probleme = self.radio_buttons[message_id].get()
        confirmation = messagebox.askyesno("Confirmation", "Voulez-vous vraiment envoyer cette réponse ?")
        if confirmation:
            try:
                self.db_handler.mycursor.execute("UPDATE messages SET messageversclient = %s, etat_probleme = %s WHERE id = %s", (reponse, etat_probleme, message_id))
                self.db_handler.mydb.commit()
                messagebox.showinfo("Message envoyé", "La réponse a été envoyée avec succès.")
            except mysql.connector.Error as err:
                messagebox.showerror("Erreur", f"Erreur lors de l'envoi de la réponse à la base de données : {err}")

    def afficher_infosclient_et_messages(self):
        try:
            self.db_handler.mycursor.execute("SELECT id, messagesversvendeur, utilisateur_id, ID_PRODUIT, etat_probleme, messageversclient FROM messages")
            infos_messages = self.db_handler.mycursor.fetchall()

            for i, info in enumerate(infos_messages):
                message_id = info[0]
                custom_font = ("Arial", 10)

                message_frame = tk.Frame(self.message_frame, bg="white", bd=2, relief=tk.GROOVE)
                message_frame.pack(side='top', fill='x', padx=10, pady=5)

                tk.Label(message_frame, text=f"Message ID: {message_id}", bg='white', font=custom_font).pack(anchor="w")
                tk.Label(message_frame, text=f"Message: {info[1]}", bg='white', font=custom_font).pack(anchor="w")
                tk.Label(message_frame, text=f"Utilisateur ID: {info[2]}", bg='white', font=custom_font).pack(anchor="w")
                tk.Label(message_frame, text=f"Produit ID: {info[3]}", bg='white', font=custom_font).pack(anchor="w")
                tk.Label(message_frame, text=f"État du problème: {info[4]}", bg='white', font=custom_font).pack(anchor="w")

                self.radio_buttons[message_id] = tk.StringVar(value=info[4])
                radio_encours = tk.Radiobutton(message_frame, text="En cours", variable=self.radio_buttons[message_id], value="en cours", bg='white', font=custom_font)
                radio_encours.pack(side='left')
                radio_traite = tk.Radiobutton(message_frame, text="Traité", variable=self.radio_buttons[message_id], value="traité", bg='white', font=custom_font)
                radio_traite.pack(side='left')

                self.state_entries[message_id] = tk.Entry(message_frame, width=60, bg='white', font=custom_font)
                self.state_entries[message_id].pack(side='left', padx=5, pady=5, expand=True, fill='x')

                bouton_envoyer = tk.Button(message_frame, text="Envoyer", command=lambda msg=message_id, entry=self.state_entries[message_id]: self.envoyer_reponse(msg, entry), width=10, font=custom_font)
                bouton_envoyer.pack(side='right', padx=5, pady=5)

        except mysql.connector.Error as err:
            messagebox.showerror("Erreur", f"Erreur lors de la récupération des informations de la base de données : {err}")

    def afficher_infos_utilisateurs(self):
        utilisateur_frame = tk.Frame(self.message_frame, bg='white')
        utilisateur_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        try:
            self.db_handler.mycursor.execute("SELECT id, nom_et_prenom, email, adresse FROM utilisateurs")
            infos_utilisateurs = self.db_handler.mycursor.fetchall()

            columns = [col[0] for col in self.db_handler.mycursor.description]
            treeview = ttk.Treeview(utilisateur_frame, columns=columns, show="headings")
            treeview.pack(side="top", fill="both", expand=True)

            for col in columns:
                treeview.heading(col, text=col)

            for row in infos_utilisateurs:
                treeview.insert("", "end", values=row)

        except mysql.connector.Error as err:
            messagebox.showerror("Erreur", f"Erreur lors de la récupération des informations de la base de données : {err}")

    def afficher_infos_produits(self):
        produit_frame = tk.Frame(self.message_frame, bg='white')
        produit_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        try:
            self.db_handler.mycursor.execute("SELECT ID_PRODUIT, Nom, Prix, pointure_id, ID_MARQUE, garantie FROM produit")
            infos_produits = self.db_handler.mycursor.fetchall()

            columns = [col[0] for col in self.db_handler.mycursor.description]
            treeview = ttk.Treeview(produit_frame, columns=columns, show="headings")
            treeview.pack(side="top", fill="both", expand=True)

            for col in columns:
                treeview.heading(col, text=col)

            for row in infos_produits:
                treeview.insert("", "end", values=row)

        except mysql.connector.Error as err:
            messagebox.showerror("Erreur", f"Erreur lors de la récupération des informations de la base de données : {err}")

    def afficher_infos_pointure(self):
        pointure_frame = tk.Frame(self.message_frame, bg='white')
        pointure_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        try:
            self.db_handler.mycursor.execute("SELECT * FROM pointures")
            infos_pointures = self.db_handler.mycursor.fetchall()

            columns = [col[0] for col in self.db_handler.mycursor.description]
            treeview = ttk.Treeview(pointure_frame, columns=columns, show="headings")
            treeview.pack(side="top", fill="both", expand=True)

            for col in columns:
                treeview.heading(col, text=col)

            for row in infos_pointures:
                treeview.insert("", "end", values=row)

        except mysql.connector.Error as err:
            messagebox.showerror("Erreur", f"Erreur lors de la récupération des informations de la base de données : {err}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MyApp(root)
    root.mainloop()
