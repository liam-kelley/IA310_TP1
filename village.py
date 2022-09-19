import math
import random
import uuid
from collections import defaultdict

import mesa
import tornado, tornado.ioloop
from mesa import space
from mesa.time import RandomActivation
from mesa.visualization.ModularVisualization import ModularServer, VisualizationElement
from mesa.visualization.ModularVisualization import UserSettableParameter
from mesa.visualization.modules import ChartModule
from traitlets import Bool


class Village(mesa.Model):

    def __init__(self, n_wolves, n_clerics,n_hunters,n_villagers):
        mesa.Model.__init__(self)
        self.space = mesa.space.ContinuousSpace(600, 600, False)
        self.schedule = RandomActivation(self)
        dict_count = {
            Wolf:n_wolves,
            Cleric:n_clerics,
            Hunter:n_hunters,
            Villager:n_villagers
        }
        for agent_type, number in dict_count.items():
            for _ in range(number):
                self.schedule.add(agent_type(random.random() * 500, random.random() * 500, 10, int(uuid.uuid1()), self))
        
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Population": lambda village : village.count_population(),
                "Humans": lambda village : village.count_humans(),
                "Wolves": lambda village : village.count_wolves(),
                "Transformed_Wolves": lambda village : village.count_wolves_transformed()})
        self.datacollector.collect(self)

    def step(self):
        self.schedule.step()
        if self.schedule.steps >= 1000:
            self.running = False
        self.datacollector.collect(self)   
    
    #Could probably speed up simulations greatly by not counting every agent at every step
    #and updating dict_count through thransformations and kills directly from agents.
    # Issue with counting transformed wolves...
    # def count_humans(self):
    #     sum=0
    #     for agent_type, number in self.dict_count.items():
    #         if not isinstance(agent_type, Wolf):
    #             sum+=number
    #     return(number)

    def count_population(self):
        return(len([agent for agent in self.schedule.agent_buffer(shuffled=False)]))

    def count_humans(self):
        list_of_humans=[agent for agent in self.schedule.agent_buffer(shuffled=False) if not isinstance(agent, Wolf)]
        return(len(list_of_humans))

    def count_wolves(self):
        list_of_wolves=[agent for agent in self.schedule.agent_buffer(shuffled=False) if isinstance(agent, Wolf)]
        return(len(list_of_wolves))
    
    def count_wolves_transformed(self):
        list_of_wolves=[agent for agent in self.schedule.agent_buffer(shuffled=False) if isinstance(agent, Wolf) and agent.transformed]
        return(len(list_of_wolves))

class ContinuousCanvas(VisualizationElement):
    local_includes = [
        "./js/jquery.js",
        "./js/simple_continuous_canvas.js",
    ]

    def __init__(self, canvas_height=500,
                 canvas_width=500, instantiate=True):
        VisualizationElement.__init__(self)
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.identifier = "space-canvas"
        if (instantiate):
            new_element = ("new Simple_Continuous_Module({}, {},'{}')".
                           format(self.canvas_width, self.canvas_height, self.identifier))
            self.js_code = "elements.push(" + new_element + ");"

    def portrayal_method(self, obj):
        return obj.portrayal_method()

    def render(self, model):
        representation = defaultdict(list)
        for obj in model.schedule.agents:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.pos[0] - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.pos[1] - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        return representation


def wander(x, y, speed, model):
    r = random.random() * math.pi * 2
    new_x = max(min(x + math.cos(r) * speed, model.space.x_max), model.space.x_min)
    new_y = max(min(y + math.sin(r) * speed, model.space.y_max), model.space.y_min)

    return new_x, new_y

def dist(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return math.hypot(x1-x2, y1-y2)


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
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model
        self.range = 40
        self.transformed=False

    def portrayal_method(self):
        color = 'red'
        if self.transformed == False:
            rayon = 3
        else:
            rayon = 6
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": rayon}
        return portrayal

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
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model
        self.range = 30

    def portrayal_method(self):
        color = 'green'
        rayon = 3
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": rayon}
        return portrayal

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
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model
        self.range = 40

    def portrayal_method(self):
        color = 'black'
        rayon = 3
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": rayon}
        return portrayal

    def kill_wolves(self,wolves_close_to_current_agent,model):
            for wolf in wolves_close_to_current_agent:
                if wolf.transformed:
                    model.schedule.remove(wolf)

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)

        agents_close_to_current_agent=[other_agent for other_agent in self.model.schedule.agent_buffer(shuffled=False) if self != other_agent and dist(other_agent.pos,self.pos)<self.range ]
        wolves_close_to_current_agent=[other_agent for other_agent in agents_close_to_current_agent if isinstance(other_agent, Wolf)]
        self.kill_wolves(wolves_close_to_current_agent,self.model)


def run_single_server():
    chart = ChartModule([
        {"Label": "Population", "Color": "Orange"},
        {"Label": "Humans", "Color": "Blue"},
        {"Label": "Wolves", "Color": "Red"},
        {"Label": "Transformed_Wolves", "Color": "Purple"}               
                      ],
                    data_collector_name='datacollector')
    
    server = ModularServer(Village,[ContinuousCanvas(), chart],
        "Village",{"n_wolves":UserSettableParameter('slider', "n_wolves", 5, 1, 25, 1),
                   "n_clerics":UserSettableParameter('slider', "n_clerics", 1, 0, 25, 1),
                   "n_hunters":UserSettableParameter('slider', "n_hunters", 2, 0, 25, 1),
                   "n_villagers":UserSettableParameter('slider', "n_villagers", 25, 0, 50, 1)})
    server.port = 8521
    server.launch()
    tornado.ioloop.IOLoop.current().stop()


if __name__ == "__main__":
    run_single_server()
