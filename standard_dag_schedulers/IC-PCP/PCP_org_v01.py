#!/usr/bin/env Python

"""
IC-PCP profiling: software and data set (version 16 Apr. 2019)
Taal, A., Wang, J., de Laat, C., & Zhao, Z. (2019).
Zenodo. https://doi.org/10.5281/zenodo.2652669

This work is distributed under the Creative Commons
Attribution 4.0 International (CC BY 4.0) license.
"""

#https://networkx.github.io/documentation/networkx-1.10/reference/classes.digraph.html

import sys
import os
import os.path

import tempfile
import math

import networkx as nx

import re
from optparse import OptionParser

G = nx.DiGraph()
number_of_nodes = 0
step = 0
deadline = 0
instances = []
# OLD-IMPL
# n_service1_inst = 0
# n_service2_inst = 0
# n_service3_inst = 0
# NEW-IMPL
NUM_SERVICES = 3
SERVICE_RANGE = range(1, NUM_SERVICES+1)
n_services_inst = {i: 0 for i in SERVICE_RANGE}


verbose = 0
prices = []
tot_idle  = 0

def  dumpJSON(start,end):
      print("{")
      print("  \"nodes\": [")
      for u in range(start,end):
         print("        { \"order\":",str(G.nodes[u]["order"])+",")
         print("          \"name\":","\""+G.nodes[u]["name"])
         #print "          \"name\":","\""+G.nodes[u]["name"]+"\","
         #print "          \"time1\":",str(G.nodes[u]["time1"])+","
         #print "          \"time2\":",str(G.nodes[u]["time2"])+","
         #print "          \"time3\":",str(G.nodes[u]["time3"])+","
         #print "          \"EST\":",str(G.nodes[u]["EST"])+","
         #print "          \"EFT\":",str(G.nodes[u]["EFT"])+","
         #print "          \"LST\":",str(G.nodes[u]["LST"])+","
         #print "          \"LFT\":",str(G.nodes[u]["LFT"])+","
         #print "          \"assigned\":",str(G.nodes[u]["assigned"])+","
         #print "          \"Service\":",str(G.nodes[u]["Service"])+","
         #print "          \"Instance\":",str(G.nodes[u]["Instance"])+","
         #print "          \"time\":",str(G.nodes[u]["time"])
         print("        },")

      print("        { \"order\":",str(G.nodes[end]["order"])+",")
      print("          \"name\":","\""+ G.nodes[end]["name"])
      #print "          \"name\":","\""+ G.nodes[end]["name"]+"\","
      #print "          \"time1\":",str(G.nodes[end]["time1"])+","
      #print "          \"time2\":",str(G.nodes[end]["time2"])+","
      #print "          \"time3\":",str(G.nodes[end]["time3"])+","
      #print "          \"EST\":",str(G.nodes[end]["EST"])+","
      #print "          \"EFT\":",str(G.nodes[end]["EFT"])+","
      #print "          \"LST\":",str(G.nodes[end]["LST"])+","
      #print "          \"LFT\":",str(G.nodes[end]["LFT"])+","
      #print "          \"assigned\": ",str(G.nodes[end]["assigned"])+","
      #print "          \"Service\": ",str(G.nodes[end]["Service"])+","
      #print "          \"Instance\": ",str(G.nodes[end]["Instance"])+","
      #print "          \"time\": ",str(G.nodes[end]["time"])
      print("        }")
      print("  ],")
      print("  \"links\": [")

      num_edges = G.number_of_edges()
      nedge = 0
      for (u,v) in G.edges():
        nedge += 1
        print("        { \"source\":","\""+G.nodes[u]["name"]+"\",")
        print("          \"target\":","\""+G.nodes[v]["name"]+"\",")
        print("          \"throughput\":",str(G[u][v]["throughput"])+",")
        print("          \"inpath\": 0")
        if nedge<num_edges :
          print("        },")
        else :
          print("        }")

      print("    ]")
      print("}")


def checkGraphTimes():
    retVal1  = graphCheckEST( )
    retVal2  = graphCheckLFT( )
    if retVal1<0 or retVal2<0 :
        return -1
    else:
        return 0

def graphCheckEST( ):
    for n in range(0, number_of_nodes) :
        nservice  = G.nodes[n]["Service"]
        ninstance = G.nodes[n]["Instance"]    

        maxest = 0
        dominant_parent = -1
        p_iter = G.predecessors(n)
        while True :
          try:
            p = next(p_iter)
            pservice  = G.nodes[p]["Service"]
            pinstance = G.nodes[p]["Instance"]
            est = G.nodes[p]["EFT"] 
            lcost = G[p][n]["throughput"]

            if pservice == nservice :
                #if pservice == 0 or nservice == 0 :
                #    est += lcost
                if pinstance == -1 or ninstance == -1 or pinstance != ninstance :
                    est += lcost
            else:
                est += lcost           
            if est>maxest :
                maxest = est
                dominant_parent = p
          except StopIteration:
              break

        # node with no parents has zero EST

        if maxest>deadline :

            print("\n**** Wrong EST: "+"EST("+G.nodes[n]["name"]+")="+str(G.nodes[n]["EST"])+", EST from dominant parent("+G.nodes[dominant_parent]["name"]+")="+str(maxest)+"; deadline="+str(deadline))

            return -1

        elif G.nodes[n]["EST"] < maxest :

            print("\n**** EST mismatch: "+"EST("+G.nodes[n]["name"]+")="+str(G.nodes[n]["EST"])+" < "+"EST("+G.nodes[dominant_parent]["name"]+")="+str(maxest))

            return -1
        elif G.nodes[n]["EST"] > deadline:

            print("\n**** Wrong EST: "+"EST("+G.nodes[n]["name"]+")="+str(G.nodes[n]["EST"])+"> deadline="+str(deadline))

            return -1

    return 0   

                  
def graphCheckLFT(  ):
    for n in range(0, number_of_nodes) :
        nservice  = G.nodes[n]["Service"]
        ninstance = G.nodes[n]["Instance"]    

        minlft = deadline
        dominant_child = -1
        c_iter = G.successors(n)
        while True :
          try:
            c = next(c_iter)             
            cservice  = G.nodes[c]["Service"];
            cinstance = G.nodes[c]["Instance"];

            lft = G.nodes[c]["LST"]
            lcost = G[n][c]["throughput"]
                             
            if cservice == nservice :
                #if cservice == 0 or nservice == 0 :
                #    lft -= lcost
                if cinstance == -1 or ninstance == -1 or cinstance != ninstance :
                    lft -= lcost
            else:
                lft -= lcost
                            
            if lft<minlft :
                dominant_child = c
                minlft = lft

          except StopIteration:
              break

        # node with no children has LFT equals deadline

        if minlft<0 :

            print("\n**** Negative LFT : "+"LFT("+G.nodes[n]["name"]+")="+str(G.nodes[n]["LFT"])+" LFT from dominant child("+G.nodes[dominant_child]["name"]+")="+str(minlft))

            return -1

        elif G.nodes[n]["LFT"] > minlft :

            print("\n**** LFT mismatch: "+"LFT("+G.nodes[n]["name"]+")="+str(G.nodes[n]["LFT"])+" > "+"LFT("+G.nodes[dominant_child]["name"]+")="+str(minlft))

            return -1
        elif G.nodes[n]["LFT"] <0 :

            print("\n**** Negative LFT : "+"LFT("+G.nodes[n]["name"]+")="+str(G.nodes[n]["LFT"]))

            return -1
    return 0


def checkIdleTime( ):
    tot_idle = 0
    idles = "\n"
    for i in range(0, len(instances)) :
        if len(instances[i])>1:
           for j in range(0, len(instances[i])-1) :
             idle_time = G.nodes[instances[i][j+1]]["EST"]-G.nodes[instances[i][j]]["EFT"]
             if idle_time>0 :
                 tot_idle += idle_time
                 idles += "\n Instance["+str(i)+"] constains idle time: "+"EST("+G.nodes[instances[i][j+1]]["name"]+")-EFT("+G.nodes[instances[i][j]]["name"]+")>0"
    print(idles)
    return tot_idle


def splitInstances( ):
    global G, instances
    new_instances = []
    for i in range(0, len(instances)) :
        if len(instances[i])>1:
           split_index = []
           split_instances = []
           for j in range(0, len(instances[i])-1) :
             comm_time = G[instances[i][j]][instances[i][j+1]]["throughput"]
             idle_time = G.nodes[instances[i][j+1]]["EST"]-G.nodes[instances[i][j]]["EFT"]
             if idle_time>0 :
                 if idle_time>=comm_time :
                     split_index.append(j+1)
                     print("split instance("+str(i)+") at index "+str(j+1)+" idle_time="+str(idle_time)+" througput="+str(comm_time))
                     #adjust throughput
                     G[instances[i][j]][instances[i][j+1]]["throughput"] = idle_time
           if len(split_index)>0: 
               prev = 0
               for k in range(0,len(split_index)):
                   new_instances.append(instances[i][prev:split_index[k]])
                   prev = split_index[k]
               new_instances.append(instances[i][prev:])
           else:
                new_instances.append(instances[i])
        else:
            new_instances.append(instances[i])
    if len(new_instances)>0:
        instances = []
        for i in range(0, len(new_instances)) :
            instances.append(new_instances[i])
    adjustInstanceAttributes( )
    return


def updateGraphTimes():
    graphAssignEST( number_of_nodes-1 )
    graphAssignLFT( 0 )

visited = []

def graphAssignEST( d ):
    global visited
    visited = []
    for i in range(0,number_of_nodes):
       visited.append(0)
    graphCalcEFT( d )


def graphCalcEFT( d ):
    global G, visited

    if verbose>1:
        print("graphCalcEFT("+str(d)+")")

    if visited[d] == 1 :
        return G.nodes[d]["EFT"]

    visited[d] = 1
    nservice  = G.nodes[d]["Service"]
    ninstance = G.nodes[d]["Instance"]

    maxest = 0
   
    predecessors = []
    p_iter = G.predecessors( d )
    while True:
        try:
            p = next(p_iter)
            predecessors.append(p)
        except StopIteration:
            break
    
    if verbose>1 :    
        print("predecessors("+str(d)+"):",predecessors)
    for p in predecessors :
           pservice  = G.nodes[p]["Service"]
           pinstance = G.nodes[p]["Instance"]

           if verbose>1 :
               print("a) graphCalcEFT( "+str(p)+" )")
           est = graphCalcEFT( p )
           if verbose>1 :
               print("a) est="+str(est)+" <-graphCalcEFT( "+str(p)+" )")

           lcost = G[p][d]["throughput"]
           
           if pservice == nservice :
              if pservice == 0 or nservice == 0 :
                  est += lcost
              elif pinstance == -1 or ninstance == -1 or pinstance != ninstance :
                est += lcost
           else:
              est += lcost 
           if est>maxest :
              maxest = est
                      
    # node with no parents has zero EST
    ceft = maxest

    G.nodes[d]["EST"] = ceft
    # OLD-IMPL
    # if nservice == 0 :
    #     ceft += G.nodes[d]["time1"]
    # elif nservice == 1 :
    #     ceft += G.nodes[d]["time1"]
    # elif nservice == 2 :
    #     ceft += G.nodes[d]["time2"]
    # elif nservice == 3 :
    #     ceft += G.nodes[d]["time3"]
    # else:
    #     ceft += G.nodes[d]["time1"]
    # NEW-IMPL
    time_key = f"time{nservice}" if nservice in SERVICE_RANGE else "time1"
    ceft += G.nodes[d][time_key]
    

    G.nodes[d]["EFT"] = ceft

    if verbose>1:
        print(G.nodes[d]["name"]+": EST="+str(G.nodes[d]["EST"]),",","EFT="+str(G.nodes[d]["EFT"]))

    return G.nodes[d]["EFT"]


def graphAssignLFT( d ):
    global visited
    visited = []
    for i in range(0,number_of_nodes):
           visited.append(0)
    graphCalcLST( d )


def graphAssignLFT( d ):
    global visited
    visited = []
    for i in range(0,number_of_nodes):
           visited.append(0)
    graphCalcLST( d )


def graphCalcLST( d ):
    global G, visited

    if verbose>1:
        print("graphCalcLST("+str(d)+")")

    if visited[d] == 1 :
        return G.nodes[d]["LST"]

    if verbose>1 :
        print("graphCalcLST("+str(d)+")")

    visited[d] = 1
    nservice  = G.nodes[d]["Service"]
    ninstance = G.nodes[d]["Instance"]

    minlft = deadline

    successors = []
    c_iter = G.successors( d )
    while True:
        try:
            c = next(c_iter)
            successors.append(c)
        except StopIteration:
            break

    for c in successors :
                      
            cservice  = G.nodes[c]["Service"]
            cinstance = G.nodes[c]["Instance"]

            if verbose>1 :
               print("a) graphCalcLST( "+str(c)+" )")
            lft = graphCalcLST( c )
            if verbose>1 :
               print("a) lft="+str(lft)+" <-graphCalcLST( "+str(c)+" )")

            lcost = G[d][c]["throughput"]
                                 
            if cservice == nservice :
                if cservice == 0 or nservice == 0 :
                    lft -= lcost
                elif cinstance == -1 or ninstance == -1 or cinstance != ninstance :
                    lft -= lcost
            else:
                lft -= lcost
                            
            if lft<minlft :
                minlft = lft

    # node with no children has LFT equals deadline
    clft = minlft
    G.nodes[d]["LFT"] = clft
    # OLD-IMPL
    # if nservice == 0 :
    #     clft -= G.nodes[d]["time1"]
    # elif nservice == 1 :
    #     clft -= G.nodes[d]["time1"]
    # elif nservice == 2 :
    #     clft -= G.nodes[d]["time2"]
    # elif nservice == 3 :
    #     clft -= G.nodes[d]["time3"]
    # else:
    #     clft -= G.nodes[d]["time1"]
    # NEW-IMPL
    time_key = f"time{nservice}" if nservice in SERVICE_RANGE else "time1"
    clft -= G.nodes[d][time_key]

    G.nodes[d]["LST"] = clft

    if verbose>1:
        print(G.nodes[d]["name"]+": EST="+str(G.nodes[d]["LST"]),",","EFT="+str(G.nodes[d]["LFT"]))

    return G.nodes[d]["LST"]


def printGraphTimes():
    trow = "\nname     "
    for n in range(0,number_of_nodes):
        trow += G.nodes[n]["name"]
        trow += "  "
    print(trow)

    trow = "VM       "
    for n in range(0,number_of_nodes):
        trow += str(G.nodes[n]["Service"])
        trow += "  "
    print(trow)

    trow = "perf     "
    for n in range(0,number_of_nodes):
        vm = G.nodes[n]["Service"]
        # OLD-IMPL
        # if vm == 3:
        #     trow += str(G.nodes[n]["time3"])
        # elif vm == 2:
        #     trow += str(G.nodes[n]["time2"])
        # else:
        #     trow += str(G.nodes[n]["time1"])
        # NEW-IMPL
        time_key = f"time{vm}" if vm in SERVICE_RANGE else "time1"
        trow += str(G.nodes[n][time_key])
        trow += "  "
    print(trow)

    trow = "\nEST      "
    for n in range(0,number_of_nodes):
        trow += str( G.nodes[n]["EST"] )
        trow += "  "
    print(trow)

    trow = "EFT      "
    for n in range(0,number_of_nodes):
        trow += str( G.nodes[n]["EFT"] )
        trow += "  "
    print(trow)

    trow = "LST      "
    for n in range(0,number_of_nodes):
        trow += str( G.nodes[n]["LST"] )
        trow += "  "
    print(trow)

    trow = "LFT      "
    for n in range(0,number_of_nodes):
        trow += str( G.nodes[n]["LFT"] )
        trow += "  "
    print(trow+"\n")

    trow = "EFT-EST  "
    for n in range(0,number_of_nodes):
        trow += str( G.nodes[n]["EFT"]-G.nodes[n]["EST"] )
        trow += "  "
    print(trow)

    trow = "LFT-LST  "
    for n in range(0,number_of_nodes):
        trow += str( G.nodes[n]["LFT"]-G.nodes[n]["LST"] )
        trow += "  "
    print(trow+"\n")


def printPerformances():

    trow = "\n    "
    for n in range(0,number_of_nodes):
        trow += G.nodes[n]["name"]
        trow += "  "
    print(trow)

    # OLD-IMPL
    # trow = "VM1 "
    # for n in range(0,number_of_nodes):
    #     trow += str( G.nodes[n]["time1"] )
    #     trow += "  "
    # print(trow)

    # trow = "VM2 "
    # for n in range(0,number_of_nodes):
    #     trow += str( G.nodes[n]["time2"] )
    #     trow += "  "
    # print(trow)

    # trow = "VM3 "
    # for n in range(0,number_of_nodes):
    #     trow += str( G.nodes[n]["time3"] )
    #     trow += "  "

    # print(trow+"\n")
    # NEW-IMPL
    for i in SERVICE_RANGE:
        trow = f"VM{i} "
        for n in range(0,number_of_nodes):
            trow += str( G.nodes[n][f"time{i}"] )
            trow += "  "
        print(trow)
    print("\n")


def assignParents( d ):
   if verbose>0 :
       print("\nassignParents("+G.nodes[d]["name"]+")")
   while hasUnassignedParents( d ) :
       pcp = []
       di = d
       while hasUnassignedParents( di ) :
           cp = getCriticalParent( di )
           if cp == -1 :
               break
           pcp = [cp] + pcp
           di = cp
       cpath = ""
       for j in pcp :
          cpath += " "+G.nodes[j]["name"]
       if verbose>0 :
           print("\nfound PCP("+G.nodes[d]["name"]+"): ",cpath)
       retval = assignPath( pcp )
       if retval == -1:
         return
       
       if verbose>0 :
           print("\nPCP("+G.nodes[d]["name"]+"): ",cpath,"assigned")

       updateGraphTimes()
       if verbose>0 :
           printGraphTimes( )

       for j in pcp :
           #updateSuccessors( j )
           #updatePredecessors( j )
           #if verbose>0 :
           #    print "Updated Successors and Predecessors of "+G.nodes[j]["name"]+" in path("+cpath+")"
           #    printGraphTimes( )
           assignParents( j )
   return


def hasUnassignedParents( d ):
    # unassigned parents?
    unassigned = 0
    p_iter = G.predecessors(d)
    while True :
      try:
        p = next(p_iter)
        if G.nodes[p]["assigned"] == 0:
            unassigned += 1
      except StopIteration:
        break
    if unassigned == 0 :                  
      return False
    else:
      return True

                 
def hasUnassignedChildren( d ):
    # unassigned cildren?
    unassigned = 0
    c_iter = G.successors(d)
    while True :
      try:
        c = next(c_iter)
        if G.nodes[c]["assigned"] == 0:
            unassigned += 1
      except StopIteration:
        break
    if unassigned == 0 :                  
      return False
    else:
      return True


def getCriticalParent( d ):                 
    max_time = 0
    cp = -1
    d_est = G.nodes[d]["EST"]
    p_iter = G.predecessors(d)
    while True :
      try:
        p = next(p_iter)
        if G.nodes[p]["assigned"] == 0 :
            ctime = G.nodes[p]["EFT"]
            ctime += G[p][d]["throughput"]
            if ctime >= max_time :
                max_time = ctime
                cp = p
      except StopIteration:
        break             
    return cp


def getCriticalPath( d ):
    pcp = []
    di = d
    while hasUnassignedParents( di ) :
        cp = getCriticalParent( di )
        if cp == -1 :
            break
        pcp = [cp] + pcp
        di = cp
    pcp.append(d)
    return pcp
    

def assignPath( p ):
    # OLD-IMPL
    # global G,instances,n_service1_inst,n_service2_inst,n_service3_inst
    # NEW-IMPL
    global G,instances,n_services_inst

    if len(p) == 0 :  
        print("Zero path len: no assignment possible")
        return -1
                   
    p_len = len(p)
    p_str = "path:"
    for j in p :
      p_str += " "+G.nodes[j]["name"]

    p_cas = -1
    p_cost = 2*number_of_nodes*prices[0]
    # assignment possible?
    prop_cas = getCheapestAssignment( p )
    if prop_cas == 0 : 
        if verbose> 0 :
            print("no pre assignment found for: ",p_str)
    elif prop_cas>0 :
        p_cas = prop_cas
        if verbose> 0 :
            print("pre assignment "+str(p_cas)+" for path ",p_str)
    
    if p_cas>0:
       p_time = getInstanceTime( p_cas, p )
    #    OLD-IMPL
    #    if p_cas == 1 :
    #        p_cost = p_time*prices[0]
    #    elif p_cas == 2 :
    #        p_cost = p_time*prices[1]
    #    elif p_cas == 3 :
    #        p_cost = p_time*prices[2]
       # NEW-IMPL
       p_cost = p_time*prices[p_cas-1]

    best_inst = -1
    best_inst_cas = -1
    best_inst_cost = 2*number_of_nodes*prices[0]
    if len(instances)>0 :
        for i in range(0, len(instances)) :
          inst_len = len(instances[i])
          if (p[0] in G.successors(instances[i][inst_len-1])) or (p[p_len-1] in G.predecessors(instances[i][0])):
            inst_cas = G.nodes[instances[i][0]]["Service"]
            inst_time = getInstanceTime( inst_cas, instances[i] )
            inst_cost = -1
            # OLD-IMPL
            # if inst_cas == 1 :
            #     inst_cost = inst_time*prices[0]
            # elif inst_cas == 2 :
            #     inst_cost = inst_time*prices[1]
            # elif inst_cas == 3 :
            #     inst_cost = inst_time*prices[2]
            # NEW-IMPL
            inst_cost = inst_time*prices[inst_cas-1]
            
            new_inst = []
            if G.nodes[p[0]]["EST"]>=G.nodes[instances[i][inst_len-1]]["EFT"]:
                for j in range(0,inst_len):
                    new_inst.append(instances[i][j])
                for j in range(0,p_len):
                    new_inst.append(p[j])
            elif G.nodes[p[p_len-1]]["EFT"]<=G.nodes[instances[i][0]]["EST"]:
                for j in range(0,p_len):
                    new_inst.append(p[j])
                for j in range(0,inst_len):
                    new_inst.append(instances[i][j])
            # prop_cas may differ inst_cas of old instance !
            prop_cas = getCheapestAssignment( new_inst )
            if prop_cas>0:
                new_inst_time = getInstanceTime( prop_cas, new_inst )
                new_inst_cost = -1
                # OLD-IMPL
                # if prop_cas == 1 :
                #     new_inst_cost = new_inst_time*prices[0]
                # elif prop_cas == 2 :
                #     new_inst_cost = new_inst_time*prices[1]
                # elif prop_cas == 3 :
                #     new_inst_cost = new_inst_time*prices[2]
                # NEW-IMPL
                new_inst_cost = new_inst_time*prices[prop_cas-1]
                
                if p_cas == -1:
                    if verbose>0 :
                        print("check extended instance",new_inst,"with prop_cas="+str(prop_cas))
                        print("new_inst_cost="+str(new_inst_cost),"<","best_inst_cost="+str(best_inst_cost)+"?:", end=' ')
                    if new_inst_cost<best_inst_cost:
                        best_inst = i
                        best_inst_cas = prop_cas
                        best_inst_cost = new_inst_cost
                        if verbose>0 :
                            print("Yes")
                    else:
                        if verbose>0 :
                            print("No")
                else:
                    if verbose>0 :
                        print("check extended instance",new_inst,"with prop_cas="+str(prop_cas))
                        print("new_inst_cost="+str(new_inst_cost),"<=","(inst_cost="+str(inst_cost)+"+p_cost="+str(p_cost)+")?:", end=' ')
                    if new_inst_cost<=(inst_cost+p_cost):
                        if verbose>0 :
                            print("Yes")
                        if verbose>0 :
                            print("new_inst_cost="+str(new_inst_cost),"<","best_inst_cost="+str(best_inst_cost)+"?:", end=' ')
                        if new_inst_cost<best_inst_cost:
                            best_inst = i
                            best_inst_cas = prop_cas
                            best_inst_cost = new_inst_cost
                            if verbose>0 :
                                print("Yes")
                        else:
                            if verbose>0:
                                print("No")
                    else:
                        if verbose>0:
                            print("No")
                     
    # prefer old instance
    if best_inst>=0 :
        best_inst_len = len(instances[best_inst])
        old_inst_cas = G.nodes[instances[best_inst][0]]["Service"]
        old_inst_est = G.nodes[instances[best_inst][0]]["EST"]
        old_inst_lft = G.nodes[instances[best_inst][best_inst_len-1]]["LFT"]
        # best_inst_cas may differ form old_inst_cas
        if best_inst_cas != old_inst_cas:
            for j in range(0,best_inst_len):
                G.nodes[instances[best_inst][j]]["Service"] = best_inst_cas
            if verbose>0:
                print("adjustInstanceAttributes due to new assignment of instance",str(best_inst))
            adjustInstanceAttributes( )
        best_inst_num = G.nodes[instances[best_inst][0]]["Instance"]
        add_before = False
        if G.nodes[p[0]]["EST"]>=G.nodes[instances[best_inst][best_inst_len-1]]["EFT"]:
            if verbose>0 :
                print("add path at end of old instance "+str(best_inst),"of Service "+str(best_inst_cas))
            for j in range(0,p_len):
                instances[best_inst].append(p[j])
        else:
            add_before = True
            if verbose>0 :
                print("add path at begin of old instance "+str(best_inst),"of Service "+str(best_inst_cas))
            for j in range(0,p_len):
                k = p_len-1-j
                instances[best_inst].insert(0, p[k])
        for j in p:
            G.nodes[j]["Service"]  = best_inst_cas
            G.nodes[j]["Instance"] = best_inst_num
            G.nodes[j]["assigned"] = 1
            # OLD-IMPL
            # if best_inst_cas == 1 :
            #     G.nodes[j]["time"] = G.nodes[j]["time1"]
            # elif best_inst_cas == 2 :
            #     G.nodes[j]["time"] = G.nodes[j]["time2"]    
            # elif best_inst_cas == 3 :
            #     G.nodes[j]["time"] = G.nodes[j]["time3"]
            # NEW-IMPL
            G.nodes[j]["time"] = G.nodes[j][f"time{best_inst_cas}"]

        est = old_inst_est
        # adjust EST
        if add_before :
            est = G.nodes[p[0]]["EST"]
        for j in instances[best_inst]:
            G.nodes[j]["EST"] = est
            est += G.nodes[j]["time"]
            G.nodes[j]["EFT"] = est
        # adjust LFT
        lft = G.nodes[p[p_len-1]]["LFT"] 
        if add_before :
            lft = old_inst_lft
        for j in range(0,len(instances[best_inst])):
            k = len(instances[best_inst])-1-j
            G.nodes[instances[best_inst][k]]["LFT"] = lft
            lft -= G.nodes[instances[best_inst][k]]["time"]
            G.nodes[instances[best_inst][k]]["LST"] = lft

        return 1
    elif p_cas>0 :
        if verbose>0 :
            print("add path to new instance ",str(len(instances)),"of Service "+str(p_cas))
        inst_num = -1
        new_instance = []
        for i in p :
            new_instance.append( i )
        instances.append( new_instance )
        # OLD-IMPL
        # if p_cas == 1:
        #     n_service1_inst += 1 
        #     inst_num = n_service1_inst
        # if p_cas == 2:
        #     n_service2_inst += 1 
        #     inst_num = n_service2_inst
        # if p_cas == 3:
        #     n_service3_inst += 1
        #     inst_num = n_service3_inst
        # NEW-IMPL
        n_services_inst[p_cas] += 1
        inst_num = n_services_inst[p_cas]
        
        for j in p:
            G.nodes[j]["Service"]  = p_cas
            G.nodes[j]["Instance"] = inst_num
            G.nodes[j]["assigned"] = 1
            # OLD-IMPL
            # if p_cas == 1 :
            #     G.nodes[j]["time"] = G.nodes[j]["time1"]
            # elif p_cas == 2 :
            #     G.nodes[j]["time"] = G.nodes[j]["time2"]    
            # elif p_cas == 3 :
            #     G.nodes[j]["time"] = G.nodes[j]["time3"]
            # NEW-IMPL
            G.nodes[j]["time"] = G.nodes[j][f"time{p_cas}"]

        #for j in p:
        #   print G.nodes[j]["name"],": assigned="+str(G.nodes[j]["assigned"]),"Service="+str(G.nodes[j]["Service"]),"Instance="+str(G.nodes[j]["Instance"]),"time="+str(G.nodes[j]["time"]),"EST="+str(G.nodes[j]["EST"]),"EFT="+str(G.nodes[j]["EFT"]),"LST="+str(G.nodes[j]["LST"]),"LFT="+str(G.nodes[j]["LFT"])

        est = G.nodes[p[0]]["EST"]
        for j in p:
            G.nodes[j]["EST"] = est
            est += G.nodes[j]["time"]
            G.nodes[j]["EFT"] = est
        # adjust LFT
        lft = G.nodes[p[p_len-1]]["LFT"] 
        for j in range(0,len(p)):
            k = len(p)-1-j
            G.nodes[p[k]]["LFT"] = lft
            lft -= G.nodes[p[k]]["time"]
            G.nodes[p[k]]["LST"] = lft

        return 1            
    else:         
        print("assignment failed for path",p_str)
        return -1

           
def getCheapestAssignment( p ) :
   
    if len(p) == 0 :
        return 0

    n_nodes = len(p)

    p_str = "path:"
    for j in p :
        p_str += " "+G.nodes[j]["name"]

    if verbose>0 :
        print("getCheapestAssignment("+p_str+")")

    new_best_cas  = 0
    new_best_cost = 0
    new_instance_time = 0 # NEW-IMPL seems to be missing in the original implementation (ERROR in line 929)
    # OLD-IMPL
    # if checkClusterLimits( 1, p ):
    #     new_best_cas = 1
    #     new_instance_time = getInstanceTime( 1, p )
    #     new_best_cost = new_instance_time*prices[0]
    
    # if checkClusterLimits( 2, p ):
    #     new_best_cas = 2
    #     new_instance_time = getInstanceTime( 2, p )
    #     new_best_cost = new_instance_time*prices[1]

    # if checkClusterLimits( 3, p ): 
    #     new_best_cas = 3
    #     new_instance_time = getInstanceTime( 3, p )
    #     new_best_cost = new_instance_time*prices[2]
    # NEW-IMPL
    for i in SERVICE_RANGE:
        if checkClusterLimits( i, p ): 
            new_best_cas = i
            new_instance_time = getInstanceTime( i, p )
            new_best_cost = new_instance_time*prices[i-1]

    if new_best_cas>0 :
        if verbose>0 :
            print("proposal assignment "+str(new_best_cas)+"("+str(new_instance_time)+") for "+p_str)
    else:
        if verbose>0 :
            print("proposal assignment "+str(new_best_cas)+" for "+p_str)
                      
    if verbose>0 :        
        print("cheapest assignment "+str(new_best_cas)+" for "+p_str)

    return new_best_cas


def checkClusterLimits( l, p ) :

    p_len = len(p)
    lft_limit_p = G.nodes[ p[p_len-1] ]["LFT"]
    est_p = G.nodes[p[0]]["EST"]
    
    if verbose>0 :
      print("checkClusterLimits for service "+str(l))

    possible = True
    
    incr_inst_time = 0
    for i in range(0,len(p)) :

        pi_time = 0
        # OLD-IMPL
        # if l==1 :
        #     pi_time = G.nodes[p[i]]["time1"]
        # elif l==2 :
        #     pi_time = G.nodes[p[i]]["time2"]
        # elif l==3 :
        #     pi_time = G.nodes[p[i]]["time3"]
        # else:
        #     pi_time = G.nodes[p[i]]["time1"]
        # NEW-IMPL
        time_key = f"time{l}" if l in SERVICE_RANGE else "time1"
        pi_time = G.nodes[p[i]][time_key]

        incr_inst_time += pi_time
        
        inst_eft = est_p + incr_inst_time
        if verbose>0 :
            print("R1 p["+str(i)+"]="+G.nodes[p[i]]["name"]+": inst_eft="+str(inst_eft)+">LFT("+str(G.nodes[p[i]]["name"])+")="+str(G.nodes[p[i]]["LFT"])+"?", end=' ')
        if inst_eft>G.nodes[p[i]]["LFT"] :
            if verbose>0 :
                print(" Yes")
            possible = False
            return possible  
        else:
            if verbose>0 :
                print(" No")
 
    return possible


def getInstanceTime( c, p ):
    inst_time = 2*deadline
                      
    if len(p)>0 :
        inst_time = 0
        for i in p :
        # OLD-IMPL
        #    if c == 1 :                    
        #        inst_time +=  G.nodes[i]["time1"]
        #    elif c == 2 :
        #        inst_time +=  G.nodes[i]["time2"]
        #    elif c == 3 :
        #        inst_time +=  G.nodes[i]["time3"]
        #    else:
        #        inst_time +=  deadline
        # NEW-IMPL
            if c in SERVICE_RANGE:
                inst_time +=  G.nodes[i][f"time{c}"]
            else:
                inst_time +=  deadline
                     
    return inst_time


def adjustInstanceAttributes( ):
    # OLD-IMPL
    # global G, instances, n_service1_inst,n_service2_inst,n_service3_inst
    # NEW-IMPL
    global G, instances, n_services_inst
    
    # OLD-IMPL
    # n_service1_inst = 0
    # n_service2_inst = 0
    # n_service3_inst = 0
    # NEW-IMPL
    n_services_inst = {i: 0 for i in SERVICE_RANGE}

    for i in range(0,len(instances)):
      service = G.nodes[instances[i][0]]["Service"]
      inst_num = -1
    #   OLD-IMPL
    #   if service == 1:
    #      n_service1_inst += 1 
    #      inst_num = n_service1_inst
    #   if service == 2:
    #      n_service2_inst += 1 
    #      inst_num = n_service2_inst
    #   if service == 3:
    #      n_service3_inst += 1 
    #      inst_num = n_service3_inst
    # NEW-IMPL
      n_services_inst[service] += 1 
      inst_num = n_services_inst[service]

      for j in range(0,len(instances[i])):
          G.nodes[instances[i][j]]["Instance"] = inst_num      


def updateSuccessors( p ):
    global G
    #
    # all successors, as LST of successors applied
    if hasUnassignedChildren( p ) :
        successors = []
        c_iter = G.successors(p)
        while True :
          try:
            c = next(c_iter)
            successors.append(c)
          except StopIteration:
            break 
        for c in successors :
            #if G.nodes[c]["assigned"] == 0 or (G.nodes[c]["time1"]==0 and G.nodes[c]["time2"]==0 and G.nodes[c]["time3"]==0):
            if G.nodes[c]["assigned"] == 0 :
                ctime = G.nodes[p]["EFT"]
                ctime += G[p][c]["throughput"]
                       
                # see 1.16.2.4 this depends on the number of assigned parents
                # as updates proceeds from entry node to exit node, skip if statement
                #if ctime>G.nodes[c]["EST"] :
                G.nodes[c]["EST"] = ctime
                G.nodes[c]["EFT"] = ctime + G.nodes[c]["time1"]
                updateSuccessors( c )
                           
                          
def updatePredecessors( c ):
    global G
    if hasUnassignedParents( c ) :
        predecessors = []
        p_iter = G.predecessors(c)
        while True :
          try:
            p = next(p_iter)
            predecessors.append(p)
          except StopIteration:
            break 
        for p in predecessors :
            #if G.nodes[p]["assigned"] == 0 or (G.nodes[p]["time1"]==0 and G.nodes[p]["time2"]==0 and G.nodes[p]["time3"]==0):
            if G.nodes[p]["assigned"] == 0 :
                ctime = G.nodes[c]["LFT"]
                if G.nodes[c]["assigned"] == 1 :
                    ctime -= G.nodes[c]["time"]
                else: 
                    ctime -= G.nodes[c]["time1"]

                ctime -= G[p][c]["throughput"]
                     
                # see 1.16.2.4 this depends on the number of assigned children
                # skip if statement       
                #if ctime<G.nodes[p]["LFT"] :
                G.nodes[p]["LFT"] = ctime
                G.nodes[p]["LST"] = ctime - G.nodes[p]["time1"]
                updatePredecessors( p )

   
def updateNode( n ):
    nservice  = G.nodes[n]["Service"]
    ninstance = G.nodes[n]["Instance"]
 
    predecessors = []
    p_iter = G.predecessors(n)
    while True :
      try:
        p = next(p_iter)
        predecessors.append(p)
      except StopIteration:
        break  

    maxest = 0
    for p in predecessors :
       pservice  = G.nodes[p]["Service"];
       pinstance = G.nodes[p]["Instance"];

       est = G.nodes[p]["EFT"]
       lcost = G[p][n]["throughput"]
       if pservice == pservice :
           if pinstance == -1 or pinstance == -1 or pinstance != pinstance :
               est -= lcost
       else:
            est -= lcost  

       if est>maxest :
           maxest = est

    G.nodes[n]["EST"] = maxest
    G.nodes[n]["EFT"] = maxest
    # OLD-IMPL
    # if nservice == 1 :                    
    #     G.nodes[n]["EFT"] +=  G.nodes[n]["time1"]
    # elif nservice == 2 :
    #     G.nodes[n]["EFT"] += G.nodes[n]["time2"]
    # elif nservice == 3 :
    #     G.nodes[n]["EFT"] += G.nodes[n]["time3"]
    # else:
    #     G.nodes[n]["EFT"] +=  G.nodes[n]["time1"]
    # NEW-IMPL
    time_key = f"time{nservice}" if nservice in SERVICE_RANGE else "time1"
    G.nodes[n]["EFT"] +=  G.nodes[n][time_key]


    successors = []
    p_iter = G.successors(n)
    while True :
      try:
        p = next(p_iter)
        successors.append(p)
      except StopIteration:
        break  

    minlft = deadline
    for c in successors :
       cservice  = G.nodes[c]["Service"];
       cinstance = G.nodes[c]["Instance"];

       lft = G.nodes[c]["LST"]
       lcost = G[n][c]["throughput"]
       if cservice == nservice :
           if cinstance == -1 or ninstance == -1 or cinstance != ninstance :
               lft -= lcost
       else:
            lft -= lcost  

       if lft<minlft :
           minlft = lft

    G.nodes[n]["LFT"] = minlft
    G.nodes[n]["LST"] = minlft
    # OLD-IMPL
    # if nservice == 1 :                    
    #     G.nodes[n]["LST"] -=  G.nodes[n]["time1"]
    # elif nservice == 2 :
    #     G.nodes[n]["LST"] -= G.nodes[n]["time2"]
    # elif nservice == 3 :
    #     G.nodes[n]["LST"] -= G.nodes[n]["time3"]
    # else:
    #     G.nodes[n]["LST"] -=  G.nodes[n]["time1"]
    # NEW-IMPL
    time_key = f"time{nservice}" if nservice in SERVICE_RANGE else "time1"
    G.nodes[n]["LST"] -=  G.nodes[n][time_key]


total_cost = 0

def printResult( ):
    global prices, total_cost
    rstr = "\nPCP solution for task graph with "+str(number_of_nodes)+" nodes"
    if verbose>0 :
        for d in range(0,number_of_nodes) :
            rstr += "  S:"+str(G.nodes[d]["Service"])+","+str(G.nodes[d]["Instance"])
        rstr += "\n"

    total_cost = 0
    # calculate cost
    # OLD-IMPL
    # nS3 = 0
    # nS2 = 0
    # nS1 = 0
    # mS3 = 0
    # mS2 = 0
    # mS1 = 0
    # NEW-IMPL
    nS = {i: 0 for i in SERVICE_RANGE}
    mS = {i: 0 for i in SERVICE_RANGE}

    if len(instances)>0 :
        if verbose>0 :
            rstr += "\n    Start time    Stop time    Duration    Inst cost    Assigned tasks"
        else:
            rstr += "\n    Start time    Stop time    Duration    Inst cost    Number of nodes"

        nodes_in_inst = 0
        for inst in instances :
          if len(inst)>0:
            linst = len(inst)
            nodes_in_inst += linst
            serv = G.nodes[inst[0]]["Service"]
            ninst = G.nodes[inst[0]]["Instance"]
            est = G.nodes[inst[0]]["EST"]
            eft = G.nodes[inst[linst-1]]["EFT"]
            duration = eft -est
            rstr += "\nS"+str(serv)+","+str(ninst)
            rstr += "   "+str(est)+"    "+str(eft)+"    "+str(duration)

            #fcunits = float(duration)/float(10)
            #icunits = int(math.ceil( fcunits ))
            icunits = duration
            cost = 0
            # OLD-IMPL
            # if serv == 1 :
            #     cost = icunits*prices[0]
            #     nS1 += 1
            #     mS1 += len(inst)
            # elif serv == 2:
            #     cost = icunits*prices[1]
            #     nS2 += 1
            #     mS2 += len(inst)
            # elif serv == 3:
            #     cost = icunits*prices[2]
            #     nS3 += 1
            #     mS3 += len(inst)
            # NEW-IMPL
            if serv in SERVICE_RANGE:
                cost = icunits*prices[serv-1]
                nS[serv] += 1
                mS[serv] += len(inst)

            total_cost += cost
            rstr += "    "+str(cost)
            tasklist = ""
            if verbose>0 :  
                for k in range(0,linst) :
                    if k>0 :
                        tasklist += ", "
                    tasklist += G.nodes[inst[k]]["name"]
            else:
                for k in range(0,linst) :
                    if k>0 :
                        tasklist += ", "
                    tasklist += G.nodes[inst[k]]["name"]
                #rstr += "    "+str(linst)              
            rstr += "    "+tasklist
        print(rstr)
        tot_non_inst = 0
        extra_cost = 0
        print("\ntotal instance cost: "+str(total_cost))
        if( nodes_in_inst != number_of_nodes ) :
           nonp = getNonInstanceNodes(   )
           nonstr = ""

           for j in range(0,number_of_nodes):
               if nonp[j]==0 :
                   nonstr += ","+G.nodes[j]["name"]
                   extra_cost += G.nodes[j]["time1"]*prices[0]
                   tot_non_inst += 1
           print("\nnon instance nodes: n="+str(tot_non_inst)+" "+nonstr[1:]+" with extra cost: "+str(extra_cost))
           total_cost += extra_cost
        tot_idle = checkIdleTime()
        if tot_idle>0:
            print("\nTotal cost: "+str(total_cost)+" for "+str(number_of_nodes),"nodes with tot idle="+str(tot_idle))
        else:
            print("\nTotal cost: "+str(total_cost)+" for "+str(number_of_nodes),"nodes")        
        # OLD-IMPL
        # m1 = 0.
        # m2 = 0.
        # m3 = 0.
        # NEW-IMPL
        m = {i: 0. for i in SERVICE_RANGE}

        # OLD-IMPL
        # if extra_cost>0:
        #   nS1 += tot_non_inst
        #   mS1 += tot_non_inst
        # NEW-IMPL
        if extra_cost>0:
          nS[1] += tot_non_inst
          mS[1] += tot_non_inst
        
        # OLD-IMPL
        # if nS1>0:
        #   m1 = float(mS1)/float(nS1)
        # if nS2>0 :
        #   m2 = float(mS2)/float(nS2)
        # if nS3>0:
        #   m3 = float(mS3)/float(nS3)
        # print("\n(#,<>)","S1:("+str(nS1)+","+str(round(m1,2))+")","S2:("+str(nS2)+","+str(round(m2,2))+")","S3:("+str(nS3)+","+str(round(m3,2))+")")
        # print("\n\t"+str(total_cost)+"\t"+str(G.nodes[number_of_nodes-1]["EFT"])+"\t("+str(nS1)+","+str(round(m1,2))+")\t("+str(nS2)+","+str(round(m2,2))+")\t("+str(nS3)+","+str(round(m3,2))+")")
        # NEW-IMPL
        for nS_key, nS_value in nS.items():
            if nS_value > 0:
                m[nS_key] = float(mS[nS_key])/float(nS[nS_key]) 
        print("\n(#,<>)", end=" ")
        for i in SERVICE_RANGE:
            print(f"S{i}:({nS[i]},{round(m[i], 2)})", end=" ")
        print(f'\n\t{total_cost}\t{G.nodes[number_of_nodes-1]["EFT"]}', end=" ")
        for i in SERVICE_RANGE:
            print(f"\t{nS[i]},{round(m[i], 2)})", end=" ")

    else:
        print("**** No instances found ****")

		# NEW-IMPL this seems not to be used, so I did not update that (now we use sum_times[] but they are not defined in the rest of this method, and it is not a global variable)
        sum_time1 = 0
        for u in G.nodes():
            sum_time1 += G.nodes[u]["time1"]
        total_cost = sum_time1*prices[0]


def getNonInstanceNodes(   ):
    nonp = []
    for j in range(0,number_of_nodes):
       nonp.append(0)
    for inst in instances :
          if len(inst)>0:
            for j in inst:
                nonp[j] = 1
    return nonp
                       
#### the main function starts here... 
def main(argv):
    global verbose, G, number_of_nodes, deadline, prices
    usage = "usage: %prog options name"
    parser = OptionParser(usage)
    parser.set_defaults(runs=1, iters=1)
    parser.add_option("-d", "--dir",   dest="dir", help="specify input directory", type="string", default="input")
    parser.add_option("-i", "--file",   dest="file", help="specify input file", type="string", default="")
    parser.add_option("-j", "--jason",  dest="json", help="dump json file", type="int", default="0")
    parser.add_option("-p", "--perc",  dest="perc", help="cp percentage deadline", type="int", default="-1")
    parser.add_option("-v", "--verbose",  dest="verbose", help="verbose output", type="int", default="0")
    (options, args) = parser.parse_args()

    dag_file = ''
    perf_file = ''
    deadline_file = ''
    price_file = ''

    if options.file:
        dag_file  = options.dir+'/'+options.file+'/'+options.file+'.propfile'
        perf_file = options.dir+'/'+options.file+'/performance'
        deadline_file = options.dir+'/'+options.file+'/deadline'
        price_file = options.dir+'/'+options.file+'/price'
    else:
        sys.exit("\nERROR - Missing option -f or --file.\n")
    verbose = options.verbose

    print("Open file '",dag_file,"'")

    f = open(dag_file, 'r')

    for line in f:
        if line.find( "->" )>-1 :
            #print line,
            line = line.strip(' ')
            line = line.rstrip('\t')
            line = line.rstrip('\n')
            line = line.rstrip('\r')
            line_arr = line.split('\t')
            #l_parsed = ''
            #for i in xrange(len(line_arr)) :
            #    l_parsed += " '" + line_arr[i] +"'"    
            #print l_parsed
            node_arr = line_arr[1].split(' ')
            node0 = int(node_arr[0])
            node1 = int(node_arr[2])
            if not G.has_node(node0) :
              G.add_node( node0 )
              G.nodes[node0]["order"] = node0
              G.nodes[node0]["name"] = "t"+str(node0)
            #   OLD-IMPL
            #   G.nodes[node0]["time1"] = 0
            #   G.nodes[node0]["time2"] = 0
            #   G.nodes[node0]["time3"] = 0
            #   NEW-IMPL
              for i in SERVICE_RANGE:               
                G.nodes[node0][f"time{i}"] = 0

            if not G.has_node(node1) :
              G.add_node( node1 )
              G.nodes[node1]['order'] = node1
              G.nodes[node1]["name"] = "t"+str(node1)
            #   OLD-IMPL
            #   G.nodes[node1]["time1"] = 0
            #   G.nodes[node1]["time2"] = 0
            #   G.nodes[node1]["time3"] = 0
            #   NEW-IMPL
              for i in SERVICE_RANGE:               
                G.nodes[node1][f"time{i}"] = 0
                
            wstr = line_arr[2].strip(' ')
            wstr = wstr.rstrip(';')
            wstr = wstr.rstrip(']')
            wstr = wstr.rstrip('0')
            wstr = wstr.rstrip('.')
            wval_arr = wstr.split('=')
            G.add_edge(node0, node1 )
            G[node0][node1]['throughput'] = int(wval_arr[1])
    f.close
    
    number_of_nodes = G.number_of_nodes()

    f = open(perf_file, 'r')
    t = 0
    for line in f:
        line = line.strip(' ')
        line = line.rstrip('\n')
        line = line.rstrip('\r')
        t += 1
        tstr = "time"+str(t)
        perf_arr = line.split(',')
        print(tstr,perf_arr)
        for inode in range(0,number_of_nodes):
        #    OLD-IMPL
        #    G.nodes[inode][tstr] = int(perf_arr[inode])
        #    NEW-IMPL
           G.nodes[inode][tstr] = float(perf_arr[inode])
    f.close

    # two reasons for adding entry node
    # a) no entry node present
    # b) current entry node has non-zero performance
    inlist = list( G.in_degree())
    print(inlist)
    num_zero = 0
    for j in inlist :
      if j[1] == 0 :
        num_zero += 1
    if num_zero>1 or (num_zero == 1 and G.nodes[0]["time1"]>0 ):
        if num_zero>1:
            print("Add entry node to graph; dag file has no entry node")
        else:
            print("Add entry node to graph; dag file has entry node with non-zero performance")
        G1=nx.DiGraph()       
        for u in G.nodes():
            unum   = u+1
            uname  = "t"+str(unum)
            uorder = unum
            G1.add_node(unum)
            G1.nodes[unum]["order"] = uorder
            G1.nodes[unum]["name"] = uname
            # OLD-IMPL
            # G1.nodes[unum]["time1"] = G.nodes[u]["time1"]
            # G1.nodes[unum]["time2"] = G.nodes[u]["time2"]
            # G1.nodes[unum]["time3"] = G.nodes[u]["time3"]
            # NEW-IMPL
            for i in SERVICE_RANGE:
                G1.nodes[unum][f"time{i}"] = G.nodes[u][f"time{i}"]
                
        for u,v in G.edges():
            G1.add_edge( u+1, v+1 )
            G1[u+1][v+1]["throughput"] = G[u][v]["throughput"]
        print("Add entry node to graph")
        G1.add_node(0)
        G1.nodes[0]["order"] = 0
        G1.nodes[0]["name"] = "t0"
        # OLD-IMPL
        # G1.nodes[0]["time1"] = 0
        # G1.nodes[0]["time2"] = 0
        # G1.nodes[0]["time3"] = 0
        # NEW-IMPL
        for i in SERVICE_RANGE:
            G1.nodes[0][f"time{i}"] = 0

        G1.nodes[0]["Service"] = 1
        G1.nodes[0]["Instance"] = -1
        for u in G1.nodes():
          if u != 0 and G1.in_degree( u ) == 0 :
            G1.add_edge( 0, u )
            G1[0][u]["throughput"] = 0
        G = G1
        number_of_nodes += 1

    # two reasons for adding exit node
    # a) no exit node present
    # b) current exit node has non-zero performance 
    outlist = list( G.out_degree())
    print(outlist)
    num_zero = 0
    for j in outlist :
        if j[1] == 0 :
            num_zero += 1

    if num_zero>1 or (num_zero == 1 and G.nodes[number_of_nodes-1]["time1"]>0 ) :
        if num_zero>1:
            print("Add exit node to graph; dag file has no exit node")
        else:
            print("Add exit node to graph; dag file has exit node with non-zero performance")
        exit_node = G.number_of_nodes()
        G.add_node( exit_node  )
        G.nodes[exit_node]["order"] = exit_node
        G.nodes[exit_node]["name"] = "t"+str(exit_node)
        # OLD-IMPL
        # G.nodes[exit_node]["time1"] = 0
        # G.nodes[exit_node]["time2"] = 0
        # G.nodes[exit_node]["time3"] = 0
        # NEW-IMPL
        for i in SERVICE_RANGE:
          G.nodes[exit_node][f"time{i}"] = 0

        G.nodes[exit_node]["Service"] = 1
        G.nodes[exit_node]["Instance"] = -1
        for u in G.nodes():
          if u != exit_node and G.out_degree( u ) == 0 :
            G.add_edge( u, exit_node )
            G[u][exit_node]["throughput"] = 0

        number_of_nodes += 1

    sum_in = 0
    for u in G.nodes():
       if G.out_degree(u)>0 :
           sum_in += G.in_degree(u)
    mean_in = float(sum_in)/float(number_of_nodes-1)
    print("Mean indegree: ",str(mean_in))

    for u in G.nodes():
      G.nodes[u]["EST"] = -1
      G.nodes[u]["EFT"] = -1
      G.nodes[u]["LST"] = -1
      G.nodes[u]["LFT"] = -1
      G.nodes[u]["assigned"] = 0
      G.nodes[u]["Service"] = 1
      G.nodes[u]["Instance"] = -1
      G.nodes[u]["time"] = G.nodes[u]["time1"]

    #check entry node and exit node
    # OLD-IMPL
    # if( G.nodes[0]["time1"]==0 and G.nodes[0]["time2"]==0 and G.nodes[0]["time3"]==0 ):
    #      G.nodes[0]["time"]=0
    #      G.nodes[0]["assigned"]=1
    # if( G.nodes[number_of_nodes-1]["time1"]==0 and G.nodes[number_of_nodes-1]["time2"]==0 and G.nodes[number_of_nodes-1]["time3"]==0 ):
    #      G.nodes[number_of_nodes-1]["time"]=0
    #      G.nodes[number_of_nodes-1]["assigned"]=1
    # NEW-IMPL
    if all(G.nodes[0][f"time{i}"] == 0 for i in SERVICE_RANGE):
      G.nodes[0]["time"]=0
      G.nodes[0]["assigned"]=1
    if all(G.nodes[number_of_nodes - 1][f"time{i}"] == 0 for i in SERVICE_RANGE):
      G.nodes[number_of_nodes-1]["time"]=0
      G.nodes[number_of_nodes-1]["assigned"]=1

    deadline = 0

    if options.json == 1 :
        dumpJSON(0,number_of_nodes-1)

    f = open(deadline_file, 'r') 
    for line in f:
        line = line.strip(' ')
        line = line.rstrip('\n')
        line = line.rstrip('\r')
        # OLD-IMPL
        # deadline = int(line)
        # NEW-IMPL
        deadline = float(line)
    f.close
    print("deadline: ",deadline)


    prices = []
    f = open(price_file, 'r') 
    for line in f:
        line = line.strip(' ')
        line = line.rstrip('\n')
        line = line.rstrip('\r')
        price_arr = line.split(',')
        for pr in price_arr :
          # OLD-IMPL
          # prices.append(int(pr))
          # NEW-IMPL
          prices.append(float(pr))
    f.close
    print("prices: ",prices)

    printPerformances()

    # OLD-IMPL
    # sum_time1 = 0
    # sum_time2 = 0
    # sum_time3 = 0
    # NEW-IMPL
    sum_times = {i:0 for i in SERVICE_RANGE}
    for u in G.nodes():
    #   OLD-IMPL
    #   sum_time1 += G.nodes[u]["time1"]
    #   sum_time2 += G.nodes[u]["time2"]
    #   sum_time3 += G.nodes[u]["time3"]
    #   NEW-IMPL
      for service_id in SERVICE_RANGE:
        sum_times[service_id] += G.nodes[u][f"time{service_id}"]

    # OLD-IMPL
    # print("sum time1: ",str(sum_time1))
    # print("sum time2: ",str(sum_time2))
    # print("sum time3: ",str(sum_time3))
    # NEW-IMPL
    for service_id in SERVICE_RANGE:
      print(f"sum time{service_id}: {sum_times[service_id]}")

    G.nodes[0]["EST"] = 0
    G.nodes[0]["EFT"] = 0 + G.nodes[0]["time1"]
    G.nodes[0]["assigned"] = 1
    G.nodes[0]["Service"] = 1
    graphAssignEST( number_of_nodes-1 )

    G.nodes[(number_of_nodes-1)]["LFT"] = deadline
    G.nodes[(number_of_nodes-1)]["LST"] = deadline - G.nodes[(number_of_nodes-1)]["time1"]
    G.nodes[(number_of_nodes-1)]["assigned"] = 1
    G.nodes[(number_of_nodes-1)]["Service"] = 1
    graphAssignLFT( 0 )

    #printGraphTimes( )

    pcp = getCriticalPath( number_of_nodes-1 )
    if len(pcp) ==  0:
        sys.exit("\nERROR **** No critical path found ****\n")

    # OLD-IMPL
    # criticali_time1 = 0
    # criticali_time2 = 0
    # criticali_time3 = 0
    # criticalp_time1 = 0
    # criticalp_time2 = 0
    # criticalp_time3 = 0
    # NEW-IMPL
    criticali_times = {i: 0 for i in SERVICE_RANGE}
    criticalp_times = {i: 0 for i in SERVICE_RANGE}

    tot_indegree = 0
    for j in range(0,len(pcp)-1):
        tot_indegree += G.in_degree(pcp[j])
        # OLD-IMPL
        # criticali_time1 += G.nodes[pcp[j]]["time1"]
        # criticali_time2 += G.nodes[pcp[j]]["time2"]
        # criticali_time3 += G.nodes[pcp[j]]["time3"]
        # NEW-IMPL
        for service_id in SERVICE_RANGE:
            criticali_times[service_id] += G.nodes[pcp[j]][f"time{service_id}"]

        throughput = G[pcp[j]][pcp[j+1]]["throughput"]
        # OLD-IMPL
        # criticalp_time1 += G.nodes[pcp[j]]["time1"] + throughput
        # criticalp_time2 += G.nodes[pcp[j]]["time2"] + throughput
        # criticalp_time3 += G.nodes[pcp[j]]["time3"] + throughput
        # NEW-IMPL
        for service_id in SERVICE_RANGE:
            criticalp_times[service_id] += G.nodes[pcp[j]][f"time{service_id}"] + throughput

    tot_indegree += G.in_degree(pcp[len(pcp)-1])
    # OLD-IMPL
    # criticali_time1 += G.nodes[pcp[len(pcp)-1]]["time1"]
    # criticali_time2 += G.nodes[pcp[len(pcp)-1]]["time2"]
    # criticali_time3 += G.nodes[pcp[len(pcp)-1]]["time3"]
    # criticalp_time1 += G.nodes[pcp[len(pcp)-1]]["time1"]
    # criticalp_time2 += G.nodes[pcp[len(pcp)-1]]["time2"]
    # criticalp_time3 += G.nodes[pcp[len(pcp)-1]]["time3"]
    # NEW-IMPL
    for i in SERVICE_RANGE:
        value = G.nodes[pcp[len(pcp)-1]][f"time{i}"]
        criticali_times[i] += value
        criticalp_times[i] += value
    
    if options.perc>0 :
      # OLD-IMPL
      # deadline = int(100.*float(criticalp_time1)/float(options.perc))
      # NEW-IMPL
      deadline = 100.*float(criticalp_times[1])/float(options.perc)
      print("new deadline: ",deadline)

    G.nodes[0]["EST"] = 0
    G.nodes[0]["EFT"] = 0 + G.nodes[0]["time1"]
    graphAssignEST( number_of_nodes-1 )

    G.nodes[(number_of_nodes-1)]["LFT"] = deadline
    G.nodes[(number_of_nodes-1)]["LST"] = deadline - G.nodes[(number_of_nodes-1)]["time1"]
    graphAssignLFT( 0 )

    print("\nStart situation")
    printGraphTimes( )

    # OLD-IMPL
    # critper1 = 100.0*float(criticalp_time1)/float(deadline)
    # critper2 = 100.0*float(criticalp_time2)/float(deadline)
    # critper3 = 100.0*float(criticalp_time3)/float(deadline)
    # critreduc1 = 100.0*float(criticali_time1)/float(deadline)
    # critreduc2 = 100.0*float(criticali_time2)/float(deadline)
    # critreduc3 = 100.0*float(criticali_time3)/float(deadline)
    # NEW-IMPL
    critpers = {i: 0. for i in SERVICE_RANGE}
    critreducs = {i: 0. for i in SERVICE_RANGE}
    for i in SERVICE_RANGE:
        critpers[i] = 100.0*float(criticalp_times[i])/float(deadline)
        critreducs[i] = 100.0*float(criticali_times[i])/float(deadline)

    mean_indegree = float(tot_indegree)/float(len(pcp))
    print("critical path: ",pcp," mean_indegree:"+str(round(mean_indegree,2)))
    # OLD-IMPL
    # print("criticalp_time(S1)="+str(criticalp_time1)+" is "+str(round(critper1,2))+"% of deadline("+str(deadline)+")")
    # print("criticalp_time(S2)="+str(criticalp_time2)+" is "+str(round(critper2,2))+"% of deadline("+str(deadline)+")")
    # print("criticalp_time(S3)="+str(criticalp_time3)+" is "+str(round(critper3,2))+"% of deadline("+str(deadline)+")")
    # print("criticali_time(S1)="+str(criticali_time1)+" is "+str(round(critreduc1,2))+"% of deadline("+str(deadline)+")")
    # print("criticali_time(S2)="+str(criticali_time2)+" is "+str(round(critreduc2,2))+"% of deadline("+str(deadline)+")")
    # print("criticali_time(S3)="+str(criticali_time3)+" is "+str(round(critreduc3,2))+"% of deadline("+str(deadline)+")")
    # NEW-IMPL
    for i in SERVICE_RANGE:
        print(f"criticalp_time(S{i})={criticalp_times[i]} is {round(critpers[i],2)}% of deadline({deadline})")
    for i in SERVICE_RANGE:
        print(f"criticali_time(S{i})={criticali_times[i]} is {round(critreducs[i],2)}% of deadline({deadline})")

    # OLD-IMPL
    # start_str = "start configuartion: cost="+str(sum_time1*prices[0])+"  EFT(exit)="+str(G.nodes[(number_of_nodes-1)]["EFT"])
    # NEW-IMPL
    start_str = "start configuartion: cost="+str(sum_times[1]*prices[0])+"  EFT(exit)="+str(G.nodes[(number_of_nodes-1)]["EFT"])

    # OLD-IMPL
    # critical_str = str(deadline)+"\t"+str(round(critper1,2))+"("+str(round(critreduc1,2))+")%"
    # critical_str += "\t"+str(round(critper2,2))+"("+str(round(critreduc2,2))+")%"
    # critical_str += "\t"+str(round(critper3,2))+"("+str(round(critreduc3,2))+")%"
    # NEW-IMPL
    critical_str = str(deadline)
    for i in SERVICE_RANGE:
        critical_str += f"\t{round(critpers[i],2)} {round(critreducs[i],2)}%"

    assignParents( number_of_nodes-1 )
    print("\nEnd situation")
    printGraphTimes( )
  
    # entry and exit node not part of PCP, so
    # adjust LST, LFT of entry node
    # adjust EST, EFT of exit node
    updateNode(0)
    updateNode(number_of_nodes-1)

    # check PCP end situation

    retVal = checkGraphTimes()
    print("checkGraphTimes: retVal="+str(retVal))
    
    if retVal<0 :
       print("\n**** Try correction sweep ****")

       updateGraphTimes()
       retVal = checkGraphTimes()
       if retVal<0 :
          print("\n**** No valid solution found after correction sweep ****")
       else:
          print("\n**** Correction sweep successful ****")

    if retVal == -1 :
        print("\nFinal situation")

        printGraphTimes()

        print("\n"+start_str)
        print("\n**** Invalid final configuration ****")
    else:

       tot_idle = checkIdleTime()
       if tot_idle>0:
            print("\n**** Try to split instances with idle time ****")
            splitInstances()
            updateGraphTimes()
            printGraphTimes( )
            retval = checkGraphTimes()
            if retVal<0 :
                print("\n**** Split failed ****")
            else:
                print("\n**** Split successful ****")
       if retVal == -1 :
           print("\nFinal situation")

           printGraphTimes()

           print("\n"+start_str)
           print("\n**** Invalid final configuration ****")
       else:
          checkIdleTime()
          printResult()
          print("\n"+start_str)
          print("final configuration:",critical_str)
          print("final configuration: cost="+str(total_cost)+"  EFT(exit)="+str(G.nodes[(number_of_nodes-1)]["EFT"]))
#############################
# The program starts here...
#############################
if __name__ == '__main__':
         
     main(sys.argv[1:])
        
#############################
# end of the program
#############################
    
