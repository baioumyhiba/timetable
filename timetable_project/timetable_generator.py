import mysql.connector
import pandas as pd
import random
import json

# Step 1: Connect to MySQL Database
db = mysql.connector.connect(
    host="localhost",
    user="root",  # Change this to your MySQL username
    password="",  # Change this to your MySQL password
    database="dut"  # Change this to your actual database name
)

cursor = db.cursor(dictionary=True)  # Use dictionary=True to get column names

# Step 2: Fetch Data
cursor.execute("SELECT * FROM professeurs")
professors = cursor.fetchall()

cursor.execute("SELECT * FROM modules")
modules = cursor.fetchall()

cursor.execute("SELECT * FROM groupe_affectes")
assignments = cursor.fetchall()

cursor.execute("SELECT * FROM disponibilite_profs")
availability = cursor.fetchall()

cursor.execute("SELECT * FROM salle_ests")  # Fetch room information
rooms = cursor.fetchall()

cursor.execute("SELECT * FROM salle_dispos")  # Fetch room availability data
room_availabilities = cursor.fetchall()

# Step 3: Organize Data into a Timetable
timetable = []
days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
time_slots = ["08:30-10:30", "10:30-12:30", "14:30-16:30", "16:30-18:30"]

# Step 4: Function to Check Professor Availability
def is_professor_available(professor_id, day, time_slot):
    matin = 1 if "08:30" <= time_slot <= "12:30" else 0
    apres_midi = 1 if "14:30" <= time_slot <= "18:30" else 0

    cursor.execute(""" 
        SELECT * FROM disponibilite_profs 
        WHERE id_prof = %s AND jour = %s AND (matin = %s OR apres_midi = %s)
    """, (professor_id, day, matin, apres_midi))

    result = cursor.fetchone()
    return result is not None


# Step 5: Function to Check Room Availability
def is_room_available(room_id, day, time_slot):
    matin = 1 if "08:30" <= time_slot <= "12:30" else 0
    apres_midi = 1 if "14:30" <= time_slot <= "18:30" else 0

    cursor.execute("""
        SELECT * FROM salle_dispos
        WHERE numero = %s AND jour = %s AND (matin = %s OR apres_midi = %s)
    """, (room_id, day, matin, apres_midi))

    room_availability = cursor.fetchone()
    return room_availability is not None


# Step 6: Assign Timetable Entries
for assign in assignments:
    professor_id = assign["idProfesseur"]
    module_id = assign["idModule"]
    group_id = assign["numeroGroupe"]

    professor = next((p for p in professors if p["id"] == professor_id), None)
    module = next((m for m in modules if m["id"] == module_id), None)

    # Step 7: If Professor and Module Exist, Assign Timeslot, Day, and Room
    if professor and module:
        assigned = False
        for day in days:
            for time_slot in time_slots:
                # Check if professor is available
                if is_professor_available(professor_id, day, time_slot):
                    # Find available rooms
                    available_rooms = [room for room in rooms if is_room_available(room["id"], day, time_slot)]
                    if available_rooms:
                        room = random.choice(available_rooms)
                        timetable.append({
                            "professor": professor["nom"],
                            "module": module["intitule_module"],
                            "group": group_id,
                            "day": day,
                            "time": time_slot,
                            "room": room["TypeSalle"]
                        })
                        assigned = True
                        break
            if assigned:
                break

# Step 8: Save Timetable as JSON
with open("timetable.json", "w", encoding="utf-8") as json_file:
    json.dump(timetable, json_file, indent=4, ensure_ascii=False)

print("✅ Timetable saved as 'timetable.json'.")

# Close connection
cursor.close()
db.close()