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
time_slots = ["08:00-10:00", "10:00-12:00", "14:00-16:00", "16:00-18:00"]

# Step 4: Function to Check Professor Availability
def is_professor_available(professor_id, day, time_slot):
    matin = "matin" if "08:00" <= time_slot <= "12:00" else None
    apres_midi = "apres_midi" if "14:00" <= time_slot <= "18:00" else None
    
    print(f"Checking availability for professor {professor_id} on {day} {time_slot}")
    
    cursor.execute(""" 
        SELECT * FROM disponibilite_profs 
        WHERE id_prof = %s AND jour = %s AND (%s = 'matin' OR %s = 'apres_midi') 
    """, (professor_id, day, matin, apres_midi))
    
    result = cursor.fetchone()
    print(f"Query result: {result}")
    return result is not None

# Step 5: Function to Check Room Availability
def is_room_available(room_id, day, time_slot):
    time_period = 'matin' if "08:00" <= time_slot <= "12:00" else 'apres_midi'

    cursor.execute("""
        SELECT * FROM salle_dispos
        WHERE jour = %s AND TypeSalle = %s AND (%s = 'matin' OR %s = 'apres_midi')
    """, (day, room_id, time_period, time_period))

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
        day = random.choice(days)
        time_slot = random.choice(time_slots)

        # Check if professor is available
        if is_professor_available(professor_id, day, time_slot):
            available_rooms = [room for room in rooms if room["TypeSalle"] in [r["TypeSalle"] for r in room_availabilities if r["jour"] == day and r["TypeSalle"] == room["TypeSalle"]]]

            if available_rooms:
                room = random.choice(available_rooms)
                room_id = room["id"]

                if is_room_available(room_id, day, time_slot):
                    timetable.append({
                        "professor": professor["nom"],
                        "module": module["intitule_module"],
                        "group": group_id,
                        "day": day,
                        "time": time_slot,
                        "room": room["TypeSalle"]
                    })

# Step 8: Save Timetable as JSON
with open("timetable.json", "w", encoding="utf-8") as json_file:
    json.dump(timetable, json_file, indent=4, ensure_ascii=False)

print("✅ Timetable saved as 'timetable.json'.")

# Close connection
cursor.close()
db.close()
