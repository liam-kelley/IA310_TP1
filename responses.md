# Ajouter la lycantropie

class Village(mesa.Model):
    def __init__(self, n_villagers):
    ...
        for _ in range(5): #Add wolves
            self.schedule.add(Villager(random.random() * 500, random.random() * 500, 10, int(uuid.uuid1()), self,True))
        for _ in range(n_villagers-5): #Add villagers
            self.schedule.add(Villager(random.random() * 500, random.random() * 500, 10, int(uuid.uuid1()), self,False))
    
class Villager(mesa.Agent):
    ...
    def __init__(self, x, y, speed, unique_id: int, model: Village, wolf: bool):
        self.wolf = wolf
    ...
    def portrayal_method(self):
            if self.wolf == False:
                color = "blue"
            else:
                color = 'red'
    ...

# états de transformations

class Villager(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village, wolf: bool):
        ...
        self.transformed=False
        ...
    def portrayal_method(self):
        ...
        if self.transformed == False:
            rayon = 3
        else:
            rayon = 6
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": rayon}
        ...

    def step(self):
        if (self.transformed == False and random.random() * 100<=10):
            self.transformed = True
        ...

# Question 1

class Villager(mesa.Agent):
    ...
    def step(self):
        ...
        if self.wolf == True :
            agents_close_to_current_agent=[other_agent for other_agent in self.model.schedule.agent_buffer(shuffled=False) if self != other_agent and math.hypot(abs(other_agent.pos[0]-self.pos[0]),abs(other_agent.pos[1]-self.pos[1]))<40 and not other_agent.wolf ]
            for other_agent in agents_close_to_current_agent:
                other_agent.wolf =True
                other_agent.transformed=True

# Update au code pour une classe pour chaque type

class Village(mesa.Model):
    def __init__(self, n_villagers):
        ...
        dict = {
            Wolf:5,
            Cleric:1,
            Hunter:2,
            Villager:n_villagers
        }
        for agent_type, number in dict.items():
            for _ in range(number):
                self.schedule.add(agent_type(random.random() * 500, random.random() * 500, 10, int(uuid.uuid1()), self))
    ...

class Villager(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model

    def portrayal_method(self):
        color = "blue"
        rayon = 3
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": rayon}
        return portrayal

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)


class Wolf(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village):
        ...
        self.range = 40
        self.transformed=False

    def portrayal_method(self):
        color = 'red'
        if self.transformed == False:
            rayon = 3
        else:
            rayon = 6
        ...

    def random_transform(self):
        if ((not self.transformed) and random.random() * 100<=10):
            self.transformed = True

    def contaminate_villagers(self,humans_close_to_current_agent,model):
            for human in humans_close_to_current_agent:
                model.schedule.add(Wolf(human.pos[0], human.pos[1], 10, int(uuid.uuid1()), model))
                model.schedule.remove(human)

    def step(self):
        self.random_transform()
        
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)

        agents_close_to_current_agent=[other_agent for other_agent in self.model.schedule.agent_buffer(shuffled=False) if self != other_agent and dist(other_agent.pos,self.pos)<self.range ]
        humans_close_to_current_agent=[other_agent for other_agent in agents_close_to_current_agent if not isinstance(other_agent, Wolf)]
        self.contaminate_villagers(humans_close_to_current_agent,self.model)

class Cleric(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village):
        ...
        self.range = 30

    def portrayal_method(self):
        color = 'green'
        rayon = 3
        ...

    def heal_wolves(self,wolves_close_to_current_agent,model):
            for wolf in wolves_close_to_current_agent:
                if not wolf.transformed:
                    model.schedule.add(Villager(wolf.pos[0], wolf.pos[1], 10, int(uuid.uuid1()), model))
                    model.schedule.remove(wolf)

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)

        agents_close_to_current_agent=[other_agent for other_agent in self.model.schedule.agent_buffer(shuffled=False) if self != other_agent and dist(other_agent.pos,self.pos)<self.range ]
        wolves_close_to_current_agent=[other_agent for other_agent in agents_close_to_current_agent if isinstance(other_agent, Wolf)]
        self.heal_wolves(wolves_close_to_current_agent,self.model)

class Hunter(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village):
        ...
        self.range = 40

    def portrayal_method(self):
        color = 'black'
        rayon = 3
        ...

    def kill_wolves(self,wolves_close_to_current_agent,model):
            for wolf in wolves_close_to_current_agent:
                if wolf.transformed:
                    model.schedule.remove(wolf)

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)

        agents_close_to_current_agent=[other_agent for other_agent in self.model.schedule.agent_buffer(shuffled=False) if self != other_agent and dist(other_agent.pos,self.pos)<self.range ]
        wolves_close_to_current_agent=[other_agent for other_agent in agents_close_to_current_agent if isinstance(other_agent, Wolf)]
        self.kill_wolves(wolves_close_to_current_agent,self.model)

# Question 2

Le système converge vers les loups qui gagnent environ en 350 cycles, desfois 1 humain survit jusqu'à 700-800 ou même plus rarement 1000 cycles.
L'impact de la présence de l'apothécaire et des chasseurs est pour l'instant très négligeable. Même si ils arrivent à vaincre un ou deux loups-garous, ils finiront par se faire manger car si ils ne jouent pas avant ils ont tendance à se faire manger.
En modifiant la quantité de chaque agent, l'équilibre final pourrait être bien différent. Si ils y avait plus de cleric que de loups, les humains auraient une bonne chance de vaincre les loups-garous.

# Question 3

Comme prévu, les loups gagnent. Belle performance cependant du dernier hunter qui a fini par ce faire tuer, mais pas sans tuer quelques loups avant.

# Question 4

q4_best_case_scenario_clerics.png

Avec 25 clerics contre 5 loups, après plusieurs essais pour avoir le meilleur résultat, les clerics perdent tout de même. Ils sont vraiment faibles, avec leur plus basse portée que les loups et leur 50% de chance de perdre fâce à eux même en portée.

q4_hunters.png

Avec 25 hunters contre 5 loups, le combat est plus juste, certains hunters arrivent à se débattre et se creuser une part du canvas. Malheuresement, inexorablement ils finissent par succomber.

q4_hunters_and_clerics.png

Avec 25 hunters et 25 clerics contre 5 loups, très tristement, les humains perdent encore plus violemment que lors de l'expérience hunters. Les clerics ont un impact négatif sur la survie des humains. Les humains s'en sortent moins bien que lorsqu'il y avait pas de clerics. C'est comme si les clerics se transformaient directement en loups.

q4_hunters_and_clerics_vs_1wolf.png

Après plusieurs essais sur cette expérience avec 25 hunters et 25 clerics contre 1 loups, les humains peuvent en effet perdre, témoignant de leur faiblesse. Le plus souvent néanmoins, ils gagnent. 

# Question 5

Les paramètre les plus importants sont la portée des agents. La grande faiblesse des humains est leur portée inférieure ou égale à celle des loups qui les empêchent de battre des loups. Sans ce buff, ils restent notamment plus faibles et leur impact est minime. La quantité de loups à un impact sur la vitesse de la convergence vers un état stable.

# Question 6

Hypothèse: les clerics n'auront aucun impact. Ils sont beaucoup trop faibles avec trop peu de portée et trop peu de stratégie. 25 clerics ne gagnent déjà pas contre 5 loups.