import mysql.connector
import random
import json

# Step 1: Connect to MySQL Database
db = mysql.connector.connect(
    host="localhost",
    user="root", 
    password="",  
    database="dut" 
)

cursor = db.cursor(dictionary=True, buffered=True)

# Step 2: Fetch Data
cursor.execute("SELECT * FROM professeurs")
professors = cursor.fetchall()  

cursor.execute("""
    SELECT m.id, m.intitule_module, m.niveau, s.numeroSemestre 
    FROM modules m
    JOIN semestres s ON m.id_semestre = s.id
""")
modules = cursor.fetchall()  

cursor.execute("SELECT * FROM groupe_affectes")
assignments = cursor.fetchall()  

cursor.execute("SELECT * FROM disponibilite_profs")
availability = cursor.fetchall()  

cursor.execute("SELECT * FROM salle_ests")  
rooms = cursor.fetchall()  

cursor.execute("SELECT * FROM salle_dispos")  
room_availabilities = cursor.fetchall()  

# Step 3: Define Constants
days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
time_slots = ["08:30-10:20", "10:40-12:30", "14:30-16:20", "16:40-18:30"]

# Step 4: Define Genetic Algorithm Parameters
POPULATION_SIZE = 50  # The number of timetables (solutions) in each generation.
GENERATIONS = 200  # The number of times the population evolves.
MUTATION_RATE = 0.1  # Probability of mutation

# Step 5: Define the Chromosome Structure
def create_random_timetable(assignments, professors, modules, rooms, days, time_slots):
    timetable = []
    for assign in assignments:
        professor_id = assign["idProfesseur"]
        module_id = assign["idModule"]
        group_id = assign["numeroGroupe"]

        professor = next((p for p in professors if p["id"] == professor_id), None)
        module = next((m for m in modules if m["id"] == module_id), None)

        if professor and module:
            day = random.choice(days)
            time_slot = random.choice(time_slots)
            room = random.choice(rooms)
            timetable.append({
                "professor": f"{professor['nom']} {professor['prenom']}",
                "module": module["intitule_module"],
                "group": group_id,
                "day": day,
                "time": time_slot,
                "room": room["TypeSalle"],
                "niveau": module["niveau"],
                "semestre": module["numeroSemestre"]
            })
    return timetable

# Step 6: Define the Fitness Function
def fitness_function(timetable):
    conflicts = 0

    # Check for professor conflicts
    professor_assignments = {}
    for entry in timetable:
        key = (entry["professor"], entry["day"], entry["time"])
        if key in professor_assignments:
            conflicts += 1
        else:
            professor_assignments[key] = True

    # Check for room conflicts
    room_assignments = {}
    for entry in timetable:
        key = (entry["room"], entry["day"], entry["time"])
        if key in room_assignments:
            conflicts += 1
        else:
            room_assignments[key] = True

    # Check for group conflicts
    group_assignments = {}
    for entry in timetable:
        key = (entry["group"], entry["day"], entry["time"])
        if key in group_assignments:
            conflicts += 1
        else:
            group_assignments[key] = True

    # Fitness is inversely proportional to conflicts
    return 1 / (1 + conflicts)

# Step 7: Define Selection, Crossover, and Mutation
def selection(population, fitness_scores):
    # Select the top 50% of the population
    sorted_population = [x for _, x in sorted(zip(fitness_scores, population), key=lambda pair: pair[0], reverse=True)]
    return sorted_population[:len(population) // 2]

def crossover(parent1, parent2):
    # Combine two timetables
    child = parent1[:len(parent1) // 2] + parent2[len(parent2) // 2:]
    return child

def mutation(timetable, professors, modules, rooms, days, time_slots):
    # Randomly change some genes
    for i in range(len(timetable)):
        if random.random() < MUTATION_RATE:
            timetable[i]["day"] = random.choice(days)
            timetable[i]["time"] = random.choice(time_slots)
            timetable[i]["room"] = random.choice(rooms)["TypeSalle"]
    return timetable

# Step 8: Initialize the Population
population = [create_random_timetable(assignments, professors, modules, rooms, days, time_slots) for _ in range(POPULATION_SIZE)]

# Step 9: Run the Genetic Algorithm
for generation in range(GENERATIONS):
    # Evaluate fitness
    fitness_scores = [fitness_function(timetable) for timetable in population]

    # Select the best timetables
    selected_population = selection(population, fitness_scores)

    # Create the next generation
    next_population = []
    while len(next_population) < POPULATION_SIZE:
        parent1, parent2 = random.sample(selected_population, 2)
        child = crossover(parent1, parent2)
        child = mutation(child, professors, modules, rooms, days, time_slots)
        next_population.append(child)

    population = next_population

    # Print the best fitness score in this generation
    best_fitness = max(fitness_scores)
    print(f"Generation {generation}: Best Fitness = {best_fitness}")

# Step 10: Save the Best Timetable
best_timetable = max(population, key=fitness_function)
with open("best_timetable.json", "w", encoding="utf-8") as json_file:
    json.dump(best_timetable, json_file, indent=4, ensure_ascii=False)

print("✅ Best timetable saved as 'best_timetable.json'.")

# Close connection
cursor.close()
db.close()