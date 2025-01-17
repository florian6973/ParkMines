from simulation import Vehicle
import numpy as np
import datetime
import distance as dist

class Parking():
    def __init__(self, blocks, disposal=[[]]):
        self.blocks = blocks
        self.occupation = dict()
        self.disposal = disposal
        self.nb_of_places = sum([block.height*block.width for block in self.blocks])

        L = []
        for block in self.blocks:
            L.append(len(block.lanes))
        self.nb_max_lanes = max(L)          #lane plus longue du parking

        self.place_ratio = 2

        max_i_disposal = len(self.disposal)
        max_j_disposal = len(self.disposal[0])
        self.x_in_pw = [0]*max_j_disposal
        self.y_in_pw = [0]*max_i_disposal

        for i_disposal in range(1, max_i_disposal):   

            for j_disposal in range(max_j_disposal):

                block_id = self.disposal[i_disposal][j_disposal]

                if self.disposal[i_disposal-1][j_disposal] != block_id:
                    k = i_disposal - 1
                    while k >=0 and self.disposal[k][j_disposal] == self.disposal[i_disposal-1][j_disposal]:
                        k -= 1

                    block_id = self.disposal[k+1][j_disposal]
                    if type(block_id) == str or self.blocks[block_id].direction == "topbottom":
                        self.y_in_pw[i_disposal] = max(self.y_in_pw[i_disposal], self.y_in_pw[k+1] + self.block_height(block_id))
                    else:
                        self.y_in_pw[i_disposal] = max(self.y_in_pw[i_disposal], self.y_in_pw[k+1] + self.block_width(block_id))

        for j_disposal in range(1, max_j_disposal):   

            for i_disposal in range(max_i_disposal):

                block_id = self.disposal[i_disposal][j_disposal]

                if self.disposal[i_disposal][j_disposal-1] != block_id:
                    k = j_disposal - 1
                    while k >=0 and self.disposal[i_disposal][k] == self.disposal[i_disposal][j_disposal-1]:
                        k -= 1

                    block_id = self.disposal[k+1][j_disposal]
                    if type(block_id) == str or self.blocks[block_id].direction == "topbottom":
                        self.x_in_pw[j_disposal] = max(self.x_in_pw[j_disposal], self.x_in_pw[k+1] + self.block_width(block_id))
                    else:
                        self.x_in_pw[j_disposal] = max(self.x_in_pw[j_disposal], self.x_in_pw[k+1] + self.block_height(block_id))

        distance = dist.Distance(self)
        distance.fill_matrix_time()
        self.matrix_time = distance.matrix_time
                
                
    
    def __repr__(self):
        s = ""
        for block in self.blocks[1:]:
            s += "\n" + block.__repr__()
        
        return " - Interface :\n"+self.blocks[0].__repr__()+"\n - Parking :"+s
    
    def travel_time(self, departure, arrival):
        """
        departure : (block_id, lane_id, side)
        arrival : (block_id, lane_id, side)
        """
        if departure == arrival:
            return datetime.timedelta(0)
        else:
            if departure[2] == 'top':
                place1 = (departure[0], departure[1], 0)
            else:
                place1 = (departure[0], departure[1], 1)
            if arrival[2] == 'top':
                place2 = (arrival[0], arrival[1], 0)
            else:
                place2 = (arrival[0], arrival[1], 1)
            duree = self.matrix_time[place1[0]][place1[1]][place1[2]][place2[0]][place2[1]][place2[2]]
        return datetime.timedelta(0,duree) + datetime.timedelta(0,30, minutes=1)
    
    def block_width(self, block_id):
        if block_id == "s":
            return 1
        if block_id == "l":
            return 9
        elif block_id == "e":
            return 0
        elif type(block_id) == str and block_id[0] == "f":
            return int(block_id[1:].split(":")[0])
        return len(self.blocks[block_id].lanes)+1

    def block_height(self, block_id):
        if block_id == "s":
            return 1
        if block_id == "l":
            return 7
        elif block_id == "e":
            return 0
        elif type(block_id) == str and block_id[0] == "f":
            return int(block_id[1:].split(":")[1])
        return self.blocks[block_id].lanes[0].length*self.place_ratio + 1

class Block():
    def __init__(self, lanes, nb_lanes=None, lane_length=None, direction="topbottom"):

        if nb_lanes:
            self.lanes = []
            for i in range(1, nb_lanes+1):
                self.lanes.append(Lane(i, lane_length))
            self.nb_lanes = nb_lanes
            self.lane_length = lane_length
        else:
            self.lanes = lanes
            self.nb_lanes = len(self.lanes)
            self.lane_length = self.lanes[0].length

        self.lane_length = lane_length
        # dimensions
        self.height = len(self.lanes) # en nombre de voitures
        self.width = self.lanes[0].length # en nombre de voitures

        self.x_pos = None
        self.y_pos = None

        self.direction = direction
    
    def __repr__(self):
        # on représente les lanes horizontalement pour construire et on transpose avant d'afficher
        
        matrix = np.empty((self.height, self.width), dtype='<U5')
        for row_index, lane in enumerate(self.lanes):
            liste = lane.list_vehicles[:]
            liste = [str(item).replace('None', '-') for item in liste]
            matrix[row_index] = liste

        # les lanes sont les colonnes (la première à gauche)
        # conformément aux termes top et bottom pour les extrémités
        return matrix.__repr__()


class BlockInterface(Block):

    def __init__(self, lanes, nb_lanes=None, lane_length=None):
        super().__init__(lanes, nb_lanes, lane_length)
        self.nb_places_available = self.height
        self.targeted = [False]*self.height


    def empty_lane(self): #renvoie "full" si interface est pleine, et return premier vehicule
        for i_lane, lane in enumerate(self.lanes):
            if lane.list_vehicles[0] == None:
                return i_lane
        else:
            return "full"

    def occupied_lane(self): #renvoie "empty" si interface est pleine, et return premier vehicule
        for i_lane, lane in enumerate(self.lanes):
            if lane.list_vehicles[0] != None:
                return i_lane
        else:
            return "empty"



class Lane() :
    def __init__(self, id_lane, length, top_access = True, bottom_access = True):
        self.length = length
        self.id = id_lane
        self.list_vehicles = np.array([None]*self.length)  
        self.top_position = None                # indice de la premiere voiture occupée dans la lane (None si pas de voiture)
        self.bottom_position = None             # indice de la derniere voiture occupée dans la lane (None si pas de voiture)
        self.future_top_position = None  
        self.future_bottom_position = None      
        self.top_access = top_access
        self.bottom_access = bottom_access

    def __repr__(self):
        liste = self.list_vehicles[:]
        liste = [str(item).replace('None', '-') for item in liste]
        return liste.__repr__()

    def is_top_available(self):
        m = 1 # Maxint
        if not self.future_top_position is None:
            m = self.future_top_position
        if not self.top_position is None:
            m = min(m, self.top_position)
        return self.top_access and m > 0

    def is_bottom_available(self):
        M = -1 # Minint
        if not self.future_bottom_position is None:
            M = self.future_bottom_position
        if not self.bottom_position is None:
            M = max(M, self.bottom_position)   
        return self.bottom_access and M < self.length - 1


    def push(self, id_vehicle, coté):
        if coté == "top":
            if self.top_position == None:
                if not self.bottom_access:
                    self.list_vehicles[-1] = id_vehicle
                    self.top_position = self.length - 1
                    self.bottom_position = self.length -1
                else:
                    self.list_vehicles[self.length//2] = id_vehicle
                    self.top_position = self.length//2
                    self.bottom_position = self.length//2
            else:
                self.list_vehicles[self.top_position-1] = id_vehicle
                self.top_position -= 1

        elif coté == "bottom":
            if self.bottom_position == None:
                if not self.top_access:
                    self.list_vehicles[0] = id_vehicle
                    self.top_position = 0
                    self.bottom_position = 0
                else:
                    self.list_vehicles[self.length//2] = id_vehicle
                    self.top_position = self.length//2
                    self.bottom_position = self.length//2
            else:
                self.list_vehicles[self.bottom_position + 1] = id_vehicle
                self.bottom_position += 1

    def push_reserve(self, coté):
        if coté == "top":
            if self.future_top_position == None:
                if not self.bottom_access:
                    self.future_top_position = self.length - 1
                    self.future_bottom_position = self.length -1
                else:
                    self.future_top_position = self.length//2
                    self.future_bottom_position = self.length//2
            else:
                self.future_top_position -= 1

        elif coté == "bottom":
            if self.future_bottom_position == None:
                if not self.top_access:
                    self.future_top_position = 0
                    self.future_bottom_position = 0
                else:
                    self.future_top_position = self.length//2
                    self.future_bottom_position = self.length//2
            else:
                self.future_bottom_position += 1

    def push_cancel_reserve(self, coté):
        if coté == "top":
            if self.future_top_position != None:
                self.future_top_position += 1
                if self.future_top_position > self.future_bottom_position: # si jamais l'indice de la premiere voiture est plus grand que celui de la dernière, ca veut dire qu'il n'y a plus de voiture
                    self.future_top_position = None
                    self.future_bottom_position = None

        elif coté == "bottom":
            if self.future_bottom_position != None:
                self.future_bottom_position -= 1
                if self.future_top_position > self.future_bottom_position: # si jamais l'indice de la premiere voiture est plus grand que celui de la dernière, ca veut dire qu'il n'y a plus de voiture
                    self.future_top_position = None
                    self.future_bottom_position = None


    def pop_reserve(self, coté):
        self.push_cancel_reserve(coté)


    def pop_cancel_reserve(self, coté):
        self.push_reserve(coté)



    def pop(self, coté):
        if coté == "top":
            if self.top_position != None:
                vehicle_id = self.list_vehicles[self.top_position]
                self.list_vehicles[self.top_position] = None
                self.top_position += 1
                if self.top_position > self.bottom_position: # si jamais l'indice de la premiere voiture est plus grand que celui de la dernière, ca veut dire qu'il n'y a plus de voiture
                    self.top_position = None
                    self.bottom_position = None
                return vehicle_id

        elif coté == "bottom":
            if self.bottom_position != None:
                vehicle_id = self.list_vehicles[self.bottom_position]
                self.list_vehicles[self.bottom_position] = None
                self.bottom_position -= 1
                if self.bottom_position < self.top_position: # si jamais l'indice de la premiere voiture est plus grand que celui de la dernière, ca veut dire qu'il n'y a plus de voiture
                    self.bottom_position = None
                    self.top_position = None
                return vehicle_id






    
