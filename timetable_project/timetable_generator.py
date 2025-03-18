import mysql.connector
import random
import json

# Step 1: Connect to MySQL Database
db = mysql.connector.connect(
    host="localhost",
    user="root",  # Change this to your MySQL username
    password="",  # Change this to your MySQL password
    database="dut"  # Change this to your actual database name
)

# Create a buffered cursor to avoid "Unread result found" errors
cursor = db.cursor(dictionary=True, buffered=True)

# Step 2: Fetch Data
cursor.execute("SELECT * FROM professeurs")
professors = cursor.fetchall()  # Fetch all results

# Fetch modules with semestre information
cursor.execute("""
    SELECT m.id, m.intitule_module, m.niveau, s.numeroSemestre 
    FROM modules m
    JOIN semestres s ON m.id_semestre = s.id
""")
modules = cursor.fetchall()  # Fetch all results

cursor.execute("SELECT * FROM groupe_affectes")
assignments = cursor.fetchall()  # Fetch all results

cursor.execute("SELECT * FROM disponibilite_profs")
availability = cursor.fetchall()  # Fetch all results

cursor.execute("SELECT * FROM salle_ests")  # Fetch room information
rooms = cursor.fetchall()  # Fetch all results

cursor.execute("SELECT * FROM salle_dispos")  # Fetch room availability data
room_availabilities = cursor.fetchall()  # Fetch all results

# Step 3: Organize Data into a Timetable
timetable = []
days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
time_slots = ["08:30-10:20", "10:40-12:30", "14:30-16:20", "16:40-18:30"]  # Updated time slots

# Step 4: Function to Check Professor Availability
def is_professor_available(professor_id, day, time_slot):
    # Split the time slot into start and end times
    start_time, end_time = time_slot.split('-')
    
    # Determine if it's morning or afternoon
    matin = 1 if "08:30" <= start_time <= "12:30" else 0
    apres_midi = 1 if "14:30" <= start_time <= "18:30" else 0

    # Use a separate cursor for this query
    with db.cursor(dictionary=True, buffered=True) as temp_cursor:
        temp_cursor.execute(""" 
            SELECT * FROM disponibilite_profs 
            WHERE id_prof = %s AND jour = %s AND (matin = %s OR apres_midi = %s)
        """, (professor_id, day, matin, apres_midi))

        result = temp_cursor.fetchone()  # Fetch the result
        return result is not None


# Step 5: Function to Check Room Availability
def is_room_available(room_id, day, time_slot):
    # Split the time slot into start and end times
    start_time, end_time = time_slot.split('-')
    
    # Determine if it's morning or afternoon
    matin = 1 if "08:30" <= start_time <= "12:30" else 0
    apres_midi = 1 if "14:30" <= start_time <= "18:30" else 0

    # Use a separate cursor for this query
    with db.cursor(dictionary=True, buffered=True) as temp_cursor:
        temp_cursor.execute("""
            SELECT * FROM salle_dispos
            WHERE numero = %s AND jour = %s AND (matin = %s OR apres_midi = %s)
        """, (room_id, day, matin, apres_midi))

        room_availability = temp_cursor.fetchone()  # Fetch the result
        return room_availability is not None


# Step 6: Function to Check if Professor is Already Assigned
def is_professor_assigned(professor_id, day, time_slot, timetable):
    for entry in timetable:
        if entry["professor"] == professor_id and entry["day"] == day and entry["time"] == time_slot:
            return True
    return False


# Step 7: Function to Check if Room is Already Assigned
def is_room_assigned(room_id, day, time_slot, timetable):
    for entry in timetable:
        if entry["room"] == room_id and entry["day"] == day and entry["time"] == time_slot:
            return True
    return False


# Step 8: Function to Check if Group is Already Assigned
def is_group_assigned(group_id, day, time_slot, timetable):
    for entry in timetable:
        if entry["group"] == group_id and entry["day"] == day and entry["time"] == time_slot:
            return True
    return False


# Step 9: Assign Timetable Entries
for assign in assignments:
    professor_id = assign["idProfesseur"]
    module_id = assign["idModule"]
    group_id = assign["numeroGroupe"]

    professor = next((p for p in professors if p["id"] == professor_id), None)
    module = next((m for m in modules if m["id"] == module_id), None)

    # Step 10: If Professor and Module Exist, Assign Timeslot, Day, and Room
    if professor and module:
        assigned = False
        for day in days:
            for time_slot in time_slots:
                # Check if professor, room, and group are available and not already assigned
                if (is_professor_available(professor_id, day, time_slot) and
                   not is_professor_assigned(professor_id, day, time_slot, timetable) and
                   not is_group_assigned(group_id, day, time_slot, timetable)):

                    # Find available rooms
                    available_rooms = [room for room in rooms if is_room_available(room["id"], day, time_slot) and
                                      not is_room_assigned(room["id"], day, time_slot, timetable)]

                    if available_rooms:
                        room = random.choice(available_rooms)
                        timetable.append({
                            "professor": f"{professor['nom']} {professor['prenom']}",  # Store professor name
                            "module": module["intitule_module"],
                            "group": group_id,
                            "day": day,
                            "time": time_slot,
                            "room": room["TypeSalle"],
                            "niveau": module["niveau"],  # Add niveau
                            "semestre": module["numeroSemestre"]  # Add semestre
                        })
                        assigned = True
                        break
            if assigned:
                break

# Step 11: Save Timetable as JSON
with open("timetable.json", "w", encoding="utf-8") as json_file:
    json.dump(timetable, json_file, indent=4, ensure_ascii=False)

print("✅ Timetable saved as 'timetable.json'.")

# Close connection
cursor.close()
db.close()