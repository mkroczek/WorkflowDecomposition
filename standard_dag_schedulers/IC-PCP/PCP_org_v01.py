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
n_service1_inst = 0
n_service2_inst = 0
n_service3_inst = 0
verbose = 0
prices = []
tot_idle  = 0

def  dumpJSON(start,end):
      print "{"
      print "  \"nodes\": ["
      for u in xrange(start,end):
         print "        { \"order\":",str(G.node[u]["order"])+","
         print "          \"name\":","\""+G.node[u]["name"]
         #print "          \"name\":","\""+G.node[u]["name"]+"\","
         #print "          \"time1\":",str(G.node[u]["time1"])+","
         #print "          \"time2\":",str(G.node[u]["time2"])+","
         #print "          \"time3\":",str(G.node[u]["time3"])+","
         #print "          \"EST\":",str(G.node[u]["EST"])+","
         #print "          \"EFT\":",str(G.node[u]["EFT"])+","
         #print "          \"LST\":",str(G.node[u]["LST"])+","
         #print "          \"LFT\":",str(G.node[u]["LFT"])+","
         #print "          \"assigned\":",str(G.node[u]["assigned"])+","
         #print "          \"Service\":",str(G.node[u]["Service"])+","
         #print "          \"Instance\":",str(G.node[u]["Instance"])+","
         #print "          \"time\":",str(G.node[u]["time"])
         print "        },"

      print "        { \"order\":",str(G.node[end]["order"])+","
      print "          \"name\":","\""+ G.node[end]["name"]
      #print "          \"name\":","\""+ G.node[end]["name"]+"\","
      #print "          \"time1\":",str(G.node[end]["time1"])+","
      #print "          \"time2\":",str(G.node[end]["time2"])+","
      #print "          \"time3\":",str(G.node[end]["time3"])+","
      #print "          \"EST\":",str(G.node[end]["EST"])+","
      #print "          \"EFT\":",str(G.node[end]["EFT"])+","
      #print "          \"LST\":",str(G.node[end]["LST"])+","
      #print "          \"LFT\":",str(G.node[end]["LFT"])+","
      #print "          \"assigned\": ",str(G.node[end]["assigned"])+","
      #print "          \"Service\": ",str(G.node[end]["Service"])+","
      #print "          \"Instance\": ",str(G.node[end]["Instance"])+","
      #print "          \"time\": ",str(G.node[end]["time"])
      print "        }"
      print "  ],"
      print "  \"links\": ["

      num_edges = G.number_of_edges()
      nedge = 0
      for (u,v) in G.edges():
        nedge += 1
        print "        { \"source\":","\""+G.node[u]["name"]+"\","
        print "          \"target\":","\""+G.node[v]["name"]+"\","
        print "          \"throughput\":",str(G[u][v]["throughput"])+","
        print "          \"inpath\": 0"
        if nedge<num_edges :
          print "        },"
        else :
          print "        }"

      print "    ]"
      print "}"


def checkGraphTimes():
    retVal1  = graphCheckEST( )
    retVal2  = graphCheckLFT( )
    if retVal1<0 or retVal2<0 :
        return -1
    else:
        return 0

def graphCheckEST( ):
    for n in xrange(0, number_of_nodes) :
        nservice  = G.node[n]["Service"]
        ninstance = G.node[n]["Instance"]    

        maxest = 0
        dominant_parent = -1
        p_iter = G.predecessors(n)
        while True :
          try:
            p = p_iter.next()
            pservice  = G.node[p]["Service"]
            pinstance = G.node[p]["Instance"]
            est = G.node[p]["EFT"] 
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

            print "\n**** Wrong EST: "+"EST("+G.node[n]["name"]+")="+str(G.node[n]["EST"])+", EST from dominant parent("+G.node[dominant_parent]["name"]+")="+str(maxest)+"; deadline="+str(deadline)

            return -1

        elif G.node[n]["EST"] < maxest :

            print "\n**** EST mismatch: "+"EST("+G.node[n]["name"]+")="+str(G.node[n]["EST"])+" < "+"EST("+G.node[dominant_parent]["name"]+")="+str(maxest)

            return -1
        elif G.node[n]["EST"] > deadline:

            print "\n**** Wrong EST: "+"EST("+G.node[n]["name"]+")="+str(G.node[n]["EST"])+"> deadline="+str(deadline)

            return -1

    return 0   

                  
def graphCheckLFT(  ):
    for n in xrange(0, number_of_nodes) :
        nservice  = G.node[n]["Service"]
        ninstance = G.node[n]["Instance"]    

        minlft = deadline
        dominant_child = -1
        c_iter = G.successors(n)
        while True :
          try:
            c = c_iter.next()             
            cservice  = G.node[c]["Service"];
            cinstance = G.node[c]["Instance"];

            lft = G.node[c]["LST"]
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

            print "\n**** Negative LFT : "+"LFT("+G.node[n]["name"]+")="+str(G.node[n]["LFT"])+" LFT from dominant child("+G.node[dominant_child]["name"]+")="+str(minlft)

            return -1

        elif G.node[n]["LFT"] > minlft :

            print "\n**** LFT mismatch: "+"LFT("+G.node[n]["name"]+")="+str(G.node[n]["LFT"])+" > "+"LFT("+G.node[dominant_child]["name"]+")="+str(minlft)

            return -1
        elif G.node[n]["LFT"] <0 :

            print "\n**** Negative LFT : "+"LFT("+G.node[n]["name"]+")="+str(G.node[n]["LFT"])

            return -1
    return 0


def checkIdleTime( ):
    tot_idle = 0
    idles = "\n"
    for i in xrange(0, len(instances)) :
        if len(instances[i])>1:
           for j in xrange(0, len(instances[i])-1) :
             idle_time = G.node[instances[i][j+1]]["EST"]-G.node[instances[i][j]]["EFT"]
             if idle_time>0 :
                 tot_idle += idle_time
                 idles += "\n Instance["+str(i)+"] constains idle time: "+"EST("+G.node[instances[i][j+1]]["name"]+")-EFT("+G.node[instances[i][j]]["name"]+")>0"
    print idles
    return tot_idle


def splitInstances( ):
    global G, instances
    new_instances = []
    for i in xrange(0, len(instances)) :
        if len(instances[i])>1:
           split_index = []
           split_instances = []
           for j in xrange(0, len(instances[i])-1) :
             comm_time = G[instances[i][j]][instances[i][j+1]]["throughput"]
             idle_time = G.node[instances[i][j+1]]["EST"]-G.node[instances[i][j]]["EFT"]
             if idle_time>0 :
                 if idle_time>=comm_time :
                     split_index.append(j+1)
                     print "split instance("+str(i)+") at index "+str(j+1)+" idle_time="+str(idle_time)+" througput="+str(comm_time)
                     #adjust throughput
                     G[instances[i][j]][instances[i][j+1]]["throughput"] = idle_time
           if len(split_index)>0: 
               prev = 0
               for k in xrange(0,len(split_index)):
                   new_instances.append(instances[i][prev:split_index[k]])
                   prev = split_index[k]
               new_instances.append(instances[i][prev:])
           else:
                new_instances.append(instances[i])
        else:
            new_instances.append(instances[i])
    if len(new_instances)>0:
        instances = []
        for i in xrange(0, len(new_instances)) :
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
    for i in xrange(0,number_of_nodes):
       visited.append(0)
    graphCalcEFT( d )


def graphCalcEFT( d ):
    global G, visited

    if verbose>1:
        print "graphCalcEFT("+str(d)+")"

    if visited[d] == 1 :
        return G.node[d]["EFT"]

    visited[d] = 1
    nservice  = G.node[d]["Service"]
    ninstance = G.node[d]["Instance"]

    maxest = 0
   
    predecessors = []
    p_iter = G.predecessors( d )
    while True:
        try:
            p = p_iter.next()
            predecessors.append(p)
        except StopIteration:
            break
    
    if verbose>1 :    
        print "predecessors("+str(d)+"):",predecessors
    for p in predecessors :
           pservice  = G.node[p]["Service"]
           pinstance = G.node[p]["Instance"]

           if verbose>1 :
               print "a) graphCalcEFT( "+str(p)+" )"
           est = graphCalcEFT( p )
           if verbose>1 :
               print "a) est="+str(est)+" <-graphCalcEFT( "+str(p)+" )"

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

    G.node[d]["EST"] = ceft
    if nservice == 0 :
        ceft += G.node[d]["time1"]
    elif nservice == 1 :
        ceft += G.node[d]["time1"]
    elif nservice == 2 :
        ceft += G.node[d]["time2"]
    elif nservice == 3 :
        ceft += G.node[d]["time3"]
    else:
        ceft += G.node[d]["time1"]
       
    G.node[d]["EFT"] = ceft

    if verbose>1:
        print G.node[d]["name"]+": EST="+str(G.node[d]["EST"]),",","EFT="+str(G.node[d]["EFT"])

    return G.node[d]["EFT"]


def graphAssignLFT( d ):
    global visited
    visited = []
    for i in xrange(0,number_of_nodes):
           visited.append(0)
    graphCalcLST( d )


def graphAssignLFT( d ):
    global visited
    visited = []
    for i in xrange(0,number_of_nodes):
           visited.append(0)
    graphCalcLST( d )


def graphCalcLST( d ):
    global G, visited

    if verbose>1:
        print "graphCalcLST("+str(d)+")"

    if visited[d] == 1 :
        return G.node[d]["LST"]

    if verbose>1 :
        print "graphCalcLST("+str(d)+")"

    visited[d] = 1
    nservice  = G.node[d]["Service"]
    ninstance = G.node[d]["Instance"]

    minlft = deadline

    successors = []
    c_iter = G.successors( d )
    while True:
        try:
            c = c_iter.next()
            successors.append(c)
        except StopIteration:
            break

    for c in successors :
                      
            cservice  = G.node[c]["Service"]
            cinstance = G.node[c]["Instance"]

            if verbose>1 :
               print "a) graphCalcLST( "+str(c)+" )"
            lft = graphCalcLST( c )
            if verbose>1 :
               print "a) lft="+str(lft)+" <-graphCalcLST( "+str(c)+" )"

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
    G.node[d]["LFT"] = clft
    if nservice == 0 :
        clft -= G.node[d]["time1"]
    elif nservice == 1 :
        clft -= G.node[d]["time1"]
    elif nservice == 2 :
        clft -= G.node[d]["time2"]
    elif nservice == 3 :
        clft -= G.node[d]["time3"]
    else:
        clft -= G.node[d]["time1"]

    G.node[d]["LST"] = clft

    if verbose>1:
        print G.node[d]["name"]+": EST="+str(G.node[d]["LST"]),",","EFT="+str(G.node[d]["LFT"])

    return G.node[d]["LST"]


def printGraphTimes():
    trow = "\nname     "
    for n in xrange(0,number_of_nodes):
        trow += G.node[n]["name"]
        trow += "  "
    print trow

    trow = "VM       "
    for n in xrange(0,number_of_nodes):
        trow += str(G.node[n]["Service"])
        trow += "  "
    print trow

    trow = "perf     "
    for n in xrange(0,number_of_nodes):
        vm = G.node[n]["Service"]
        if vm == 3:
            trow += str(G.node[n]["time3"])
        elif vm == 2:
            trow += str(G.node[n]["time2"])
        else:
            trow += str(G.node[n]["time1"])
        trow += "  "
    print trow

    trow = "\nEST      "
    for n in xrange(0,number_of_nodes):
        trow += str( G.node[n]["EST"] )
        trow += "  "
    print trow

    trow = "EFT      "
    for n in xrange(0,number_of_nodes):
        trow += str( G.node[n]["EFT"] )
        trow += "  "
    print trow

    trow = "LST      "
    for n in xrange(0,number_of_nodes):
        trow += str( G.node[n]["LST"] )
        trow += "  "
    print trow

    trow = "LFT      "
    for n in xrange(0,number_of_nodes):
        trow += str( G.node[n]["LFT"] )
        trow += "  "
    print trow+"\n"

    trow = "EFT-EST  "
    for n in xrange(0,number_of_nodes):
        trow += str( G.node[n]["EFT"]-G.node[n]["EST"] )
        trow += "  "
    print trow

    trow = "LFT-LST  "
    for n in xrange(0,number_of_nodes):
        trow += str( G.node[n]["LFT"]-G.node[n]["LST"] )
        trow += "  "
    print trow+"\n"


def printPerformances():

    trow = "\n    "
    for n in xrange(0,number_of_nodes):
        trow += G.node[n]["name"]
        trow += "  "
    print trow

    trow = "VM1 "
    for n in xrange(0,number_of_nodes):
        trow += str( G.node[n]["time1"] )
        trow += "  "
    print trow

    trow = "VM2 "
    for n in xrange(0,number_of_nodes):
        trow += str( G.node[n]["time2"] )
        trow += "  "
    print trow

    trow = "VM3 "
    for n in xrange(0,number_of_nodes):
        trow += str( G.node[n]["time3"] )
        trow += "  "

    print trow+"\n"


def assignParents( d ):
   if verbose>0 :
       print "\nassignParents("+G.node[d]["name"]+")"
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
          cpath += " "+G.node[j]["name"]
       if verbose>0 :
           print "\nfound PCP("+G.node[d]["name"]+"): ",cpath
       retval = assignPath( pcp )
       if retval == -1:
         return
       
       if verbose>0 :
           print "\nPCP("+G.node[d]["name"]+"): ",cpath,"assigned"

       updateGraphTimes()
       if verbose>0 :
           printGraphTimes( )

       for j in pcp :
           #updateSuccessors( j )
           #updatePredecessors( j )
           #if verbose>0 :
           #    print "Updated Successors and Predecessors of "+G.node[j]["name"]+" in path("+cpath+")"
           #    printGraphTimes( )
           assignParents( j )
   return


def hasUnassignedParents( d ):
    # unassigned parents?
    unassigned = 0
    p_iter = G.predecessors(d)
    while True :
      try:
        p = p_iter.next()
        if G.node[p]["assigned"] == 0:
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
        c = c_iter.next()
        if G.node[c]["assigned"] == 0:
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
    d_est = G.node[d]["EST"]
    p_iter = G.predecessors(d)
    while True :
      try:
        p = p_iter.next()
        if G.node[p]["assigned"] == 0 :
            ctime = G.node[p]["EFT"]
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
    global G,instances,n_service1_inst,n_service2_inst,n_service3_inst

    if len(p) == 0 :  
        print "Zero path len: no assignment possible"
        return -1
                   
    p_len = len(p)
    p_str = "path:"
    for j in p :
      p_str += " "+G.node[j]["name"]

    p_cas = -1
    p_cost = 2*number_of_nodes*prices[0]
    # assignment possible?
    prop_cas = getCheapestAssignment( p )
    if prop_cas == 0 : 
        if verbose> 0 :
            print "no pre assignment found for: ",p_str
    elif prop_cas>0 :
        p_cas = prop_cas
        if verbose> 0 :
            print "pre assignment "+str(p_cas)+" for path ",p_str
    
    if p_cas>0:
       p_time = getInstanceTime( p_cas, p )
       if p_cas == 1 :
           p_cost = p_time*prices[0]
       elif p_cas == 2 :
           p_cost = p_time*prices[1]
       elif p_cas == 3 :
           p_cost = p_time*prices[2]

    best_inst = -1
    best_inst_cas = -1
    best_inst_cost = 2*number_of_nodes*prices[0]
    if len(instances)>0 :
        for i in xrange(0, len(instances)) :
          inst_len = len(instances[i])
          if (p[0] in G.successors(instances[i][inst_len-1])) or (p[p_len-1] in G.predecessors(instances[i][0])):
            inst_cas = G.node[instances[i][0]]["Service"]
            inst_time = getInstanceTime( inst_cas, instances[i] )
            inst_cost = -1
            if inst_cas == 1 :
                inst_cost = inst_time*prices[0]
            elif inst_cas == 2 :
                inst_cost = inst_time*prices[1]
            elif inst_cas == 3 :
                inst_cost = inst_time*prices[2]
            new_inst = []
            if G.node[p[0]]["EST"]>=G.node[instances[i][inst_len-1]]["EFT"]:
                for j in xrange(0,inst_len):
                    new_inst.append(instances[i][j])
                for j in xrange(0,p_len):
                    new_inst.append(p[j])
            elif G.node[p[p_len-1]]["EFT"]<=G.node[instances[i][0]]["EST"]:
                for j in xrange(0,p_len):
                    new_inst.append(p[j])
                for j in xrange(0,inst_len):
                    new_inst.append(instances[i][j])
            # prop_cas may differ inst_cas of old instance !
            prop_cas = getCheapestAssignment( new_inst )
            if prop_cas>0:
                new_inst_time = getInstanceTime( prop_cas, new_inst )
                new_inst_cost = -1
                if prop_cas == 1 :
                    new_inst_cost = new_inst_time*prices[0]
                elif prop_cas == 2 :
                    new_inst_cost = new_inst_time*prices[1]
                elif prop_cas == 3 :
                    new_inst_cost = new_inst_time*prices[2]
                if p_cas == -1:
                    if verbose>0 :
                        print "check extended instance",new_inst,"with prop_cas="+str(prop_cas)
                        print "new_inst_cost="+str(new_inst_cost),"<","best_inst_cost="+str(best_inst_cost)+"?:",
                    if new_inst_cost<best_inst_cost:
                        best_inst = i
                        best_inst_cas = prop_cas
                        best_inst_cost = new_inst_cost
                        if verbose>0 :
                            print "Yes"
                    else:
                        if verbose>0 :
                            print "No"
                else:
                    if verbose>0 :
                        print "check extended instance",new_inst,"with prop_cas="+str(prop_cas)
                        print "new_inst_cost="+str(new_inst_cost),"<=","(inst_cost="+str(inst_cost)+"+p_cost="+str(p_cost)+")?:",
                    if new_inst_cost<=(inst_cost+p_cost):
                        if verbose>0 :
                            print "Yes"
                        if verbose>0 :
                            print "new_inst_cost="+str(new_inst_cost),"<","best_inst_cost="+str(best_inst_cost)+"?:",
                        if new_inst_cost<best_inst_cost:
                            best_inst = i
                            best_inst_cas = prop_cas
                            best_inst_cost = new_inst_cost
                            if verbose>0 :
                                print "Yes"
                        else:
                            if verbose>0:
                                print "No"
                    else:
                        if verbose>0:
                            print "No"
                     
    # prefer old instance
    if best_inst>=0 :
        best_inst_len = len(instances[best_inst])
        old_inst_cas = G.node[instances[best_inst][0]]["Service"]
        old_inst_est = G.node[instances[best_inst][0]]["EST"]
        old_inst_lft = G.node[instances[best_inst][best_inst_len-1]]["LFT"]
        # best_inst_cas may differ form old_inst_cas
        if best_inst_cas != old_inst_cas:
            for j in xrange(0,best_inst_len):
                G.node[instances[best_inst][j]]["Service"] = best_inst_cas
            if verbose>0:
                print "adjustInstanceAttributes due to new assignment of instance",str(best_inst)
            adjustInstanceAttributes( )
        best_inst_num = G.node[instances[best_inst][0]]["Instance"]
        add_before = False
        if G.node[p[0]]["EST"]>=G.node[instances[best_inst][best_inst_len-1]]["EFT"]:
            if verbose>0 :
                print "add path at end of old instance "+str(best_inst),"of Service "+str(best_inst_cas)
            for j in xrange(0,p_len):
                instances[best_inst].append(p[j])
        else:
            add_before = True
            if verbose>0 :
                print "add path at begin of old instance "+str(best_inst),"of Service "+str(best_inst_cas)
            for j in xrange(0,p_len):
                k = p_len-1-j
                instances[best_inst].insert(0, p[k])
        for j in p:
            G.node[j]["Service"]  = best_inst_cas
            G.node[j]["Instance"] = best_inst_num
            G.node[j]["assigned"] = 1
            if best_inst_cas == 1 :
                G.node[j]["time"] = G.node[j]["time1"]
            elif best_inst_cas == 2 :
                G.node[j]["time"] = G.node[j]["time2"]    
            elif best_inst_cas == 3 :
                G.node[j]["time"] = G.node[j]["time3"]

        est = old_inst_est
        # adjust EST
        if add_before :
            est = G.node[p[0]]["EST"]
        for j in instances[best_inst]:
            G.node[j]["EST"] = est
            est += G.node[j]["time"]
            G.node[j]["EFT"] = est
        # adjust LFT
        lft = G.node[p[p_len-1]]["LFT"] 
        if add_before :
            lft = old_inst_lft
        for j in xrange(0,len(instances[best_inst])):
            k = len(instances[best_inst])-1-j
            G.node[instances[best_inst][k]]["LFT"] = lft
            lft -= G.node[instances[best_inst][k]]["time"]
            G.node[instances[best_inst][k]]["LST"] = lft

        return 1
    elif p_cas>0 :
        if verbose>0 :
            print "add path to new instance ",str(len(instances)),"of Service "+str(p_cas)
        inst_num = -1
        new_instance = []
        for i in p :
            new_instance.append( i )
        instances.append( new_instance )
        if p_cas == 1:
            n_service1_inst += 1 
            inst_num = n_service1_inst
        if p_cas == 2:
            n_service2_inst += 1 
            inst_num = n_service2_inst
        if p_cas == 3:
            n_service3_inst += 1 
            inst_num = n_service3_inst    
        for j in p:
            G.node[j]["Service"]  = p_cas
            G.node[j]["Instance"] = inst_num
            G.node[j]["assigned"] = 1
            if p_cas == 1 :
                G.node[j]["time"] = G.node[j]["time1"]
            elif p_cas == 2 :
                G.node[j]["time"] = G.node[j]["time2"]    
            elif p_cas == 3 :
                G.node[j]["time"] = G.node[j]["time3"]

        #for j in p:
        #   print G.node[j]["name"],": assigned="+str(G.node[j]["assigned"]),"Service="+str(G.node[j]["Service"]),"Instance="+str(G.node[j]["Instance"]),"time="+str(G.node[j]["time"]),"EST="+str(G.node[j]["EST"]),"EFT="+str(G.node[j]["EFT"]),"LST="+str(G.node[j]["LST"]),"LFT="+str(G.node[j]["LFT"])

        est = G.node[p[0]]["EST"]
        for j in p:
            G.node[j]["EST"] = est
            est += G.node[j]["time"]
            G.node[j]["EFT"] = est
        # adjust LFT
        lft = G.node[p[p_len-1]]["LFT"] 
        for j in xrange(0,len(p)):
            k = len(p)-1-j
            G.node[p[k]]["LFT"] = lft
            lft -= G.node[p[k]]["time"]
            G.node[p[k]]["LST"] = lft

        return 1            
    else:         
        print "assignment failed for path",p_str
        return -1

           
def getCheapestAssignment( p ) :
   
    if len(p) == 0 :
        return 0

    n_nodes = len(p)

    p_str = "path:"
    for j in p :
        p_str += " "+G.node[j]["name"]

    if verbose>0 :
        print "getCheapestAssignment("+p_str+")"

    new_best_cas  = 0
    new_best_cost = 0
    if checkClusterLimits( 1, p ):
        new_best_cas = 1
        new_instance_time = getInstanceTime( 1, p )
        new_best_cost = new_instance_time*prices[0]
    
    if checkClusterLimits( 2, p ):
        new_best_cas = 2
        new_instance_time = getInstanceTime( 2, p )
        new_best_cost = new_instance_time*prices[1]

    if checkClusterLimits( 3, p ): 
        new_best_cas = 3
        new_instance_time = getInstanceTime( 3, p )
        new_best_cost = new_instance_time*prices[2]

    if new_best_cas>0 :
        if verbose>0 :
            print "proposal assignment "+str(new_best_cas)+"("+str(new_instance_time)+") for "+p_str
    else:
        if verbose>0 :
            print "proposal assignment "+str(new_best_cas)+" for "+p_str
                      
    if verbose>0 :        
        print "cheapest assignment "+str(new_best_cas)+" for "+p_str

    return new_best_cas


def checkClusterLimits( l, p ) :

    p_len = len(p)
    lft_limit_p = G.node[ p[p_len-1] ]["LFT"]
    est_p = G.node[p[0]]["EST"]
    
    if verbose>0 :
      print "checkClusterLimits for service "+str(l)

    possible = True
    
    incr_inst_time = 0
    for i in xrange(0,len(p)) :

        pi_time = 0
        if l==1 :
            pi_time = G.node[p[i]]["time1"]
        elif l==2 :
            pi_time = G.node[p[i]]["time2"]
        elif l==3 :
            pi_time = G.node[p[i]]["time3"]
        else:
            pi_time = G.node[p[i]]["time1"]

        incr_inst_time += pi_time
        
        inst_eft = est_p + incr_inst_time
        if verbose>0 :
            print "R1 p["+str(i)+"]="+G.node[p[i]]["name"]+": inst_eft="+str(inst_eft)+">LFT("+str(G.node[p[i]]["name"])+")="+str(G.node[p[i]]["LFT"])+"?",
        if inst_eft>G.node[p[i]]["LFT"] :
            if verbose>0 :
                print " Yes"
            possible = False
            return possible  
        else:
            if verbose>0 :
                print " No"
 
    return possible


def getInstanceTime( c, p ):
    inst_time = 2*deadline
                      
    if len(p)>0 :
        inst_time = 0
        for i in p :
           if c == 1 :                    
               inst_time +=  G.node[i]["time1"]
           elif c == 2 :
               inst_time +=  G.node[i]["time2"]
           elif c == 3 :
               inst_time +=  G.node[i]["time3"]
           else:
               inst_time +=  deadline
                     
    return inst_time


def adjustInstanceAttributes( ):
    global G, instances, n_service1_inst,n_service2_inst,n_service3_inst
    n_service1_inst = 0
    n_service2_inst = 0
    n_service3_inst = 0
    for i in xrange(0,len(instances)):
      service = G.node[instances[i][0]]["Service"]
      inst_num = -1
      if service == 1:
         n_service1_inst += 1 
         inst_num = n_service1_inst
      if service == 2:
         n_service2_inst += 1 
         inst_num = n_service2_inst
      if service == 3:
         n_service3_inst += 1 
         inst_num = n_service3_inst
      for j in xrange(0,len(instances[i])):
          G.node[instances[i][j]]["Instance"] = inst_num      


def updateSuccessors( p ):
    global G
    #
    # all successors, as LST of successors applied
    if hasUnassignedChildren( p ) :
        successors = []
        c_iter = G.successors(p)
        while True :
          try:
            c = c_iter.next()
            successors.append(c)
          except StopIteration:
            break 
        for c in successors :
            #if G.node[c]["assigned"] == 0 or (G.node[c]["time1"]==0 and G.node[c]["time2"]==0 and G.node[c]["time3"]==0):
            if G.node[c]["assigned"] == 0 :
                ctime = G.node[p]["EFT"]
                ctime += G[p][c]["throughput"]
                       
                # see 1.16.2.4 this depends on the number of assigned parents
                # as updates proceeds from entry node to exit node, skip if statement
                #if ctime>G.node[c]["EST"] :
                G.node[c]["EST"] = ctime
                G.node[c]["EFT"] = ctime + G.node[c]["time1"]
                updateSuccessors( c )
                           
                          
def updatePredecessors( c ):
    global G
    if hasUnassignedParents( c ) :
        predecessors = []
        p_iter = G.predecessors(c)
        while True :
          try:
            p = p_iter.next()
            predecessors.append(p)
          except StopIteration:
            break 
        for p in predecessors :
            #if G.node[p]["assigned"] == 0 or (G.node[p]["time1"]==0 and G.node[p]["time2"]==0 and G.node[p]["time3"]==0):
            if G.node[p]["assigned"] == 0 :
                ctime = G.node[c]["LFT"]
                if G.node[c]["assigned"] == 1 :
                    ctime -= G.node[c]["time"]
                else: 
                    ctime -= G.node[c]["time1"]

                ctime -= G[p][c]["throughput"]
                     
                # see 1.16.2.4 this depends on the number of assigned children
                # skip if statement       
                #if ctime<G.node[p]["LFT"] :
                G.node[p]["LFT"] = ctime
                G.node[p]["LST"] = ctime - G.node[p]["time1"]
                updatePredecessors( p )

   
def updateNode( n ):
    nservice  = G.node[n]["Service"]
    ninstance = G.node[n]["Instance"]
 
    predecessors = []
    p_iter = G.predecessors(n)
    while True :
      try:
        p = p_iter.next()
        predecessors.append(p)
      except StopIteration:
        break  

    maxest = 0
    for p in predecessors :
       pservice  = G.node[p]["Service"];
       pinstance = G.node[p]["Instance"];

       est = G.node[p]["EFT"]
       lcost = G[p][n]["throughput"]
       if pservice == pservice :
           if pinstance == -1 or pinstance == -1 or pinstance != pinstance :
               est -= lcost
       else:
            est -= lcost  

       if est>maxest :
           maxest = est

    G.node[n]["EST"] = maxest
    G.node[n]["EFT"] = maxest
    if nservice == 1 :                    
        G.node[n]["EFT"] +=  G.node[n]["time1"]
    elif nservice == 2 :
        G.node[n]["EFT"] += G.node[n]["time2"]
    elif nservice == 3 :
        G.node[n]["EFT"] += G.node[n]["time3"]
    else:
        G.node[n]["EFT"] +=  G.node[n]["time1"]


    successors = []
    p_iter = G.successors(n)
    while True :
      try:
        p = p_iter.next()
        successors.append(p)
      except StopIteration:
        break  

    minlft = deadline
    for c in successors :
       cservice  = G.node[c]["Service"];
       cinstance = G.node[c]["Instance"];

       lft = G.node[c]["LST"]
       lcost = G[n][c]["throughput"]
       if cservice == nservice :
           if cinstance == -1 or ninstance == -1 or cinstance != ninstance :
               lft -= lcost
       else:
            lft -= lcost  

       if lft<minlft :
           minlft = lft

    G.node[n]["LFT"] = minlft
    G.node[n]["LST"] = minlft
    if nservice == 1 :                    
        G.node[n]["LST"] -=  G.node[n]["time1"]
    elif nservice == 2 :
        G.node[n]["LST"] -= G.node[n]["time2"]
    elif nservice == 3 :
        G.node[n]["LST"] -= G.node[n]["time3"]
    else:
        G.node[n]["LST"] -=  G.node[n]["time1"]

total_cost = 0
                    
def printResult( ):
    global prices, total_cost
    rstr = "\nPCP solution for task graph with "+str(number_of_nodes)+" nodes"
    if verbose>0 :
        for d in xrange(0,number_of_nodes) :
            rstr += "  S:"+str(G.node[d]["Service"])+","+str(G.node[d]["Instance"])
        rstr += "\n"

    total_cost = 0
    # calculate cost
    nS3 = 0
    nS2 = 0
    nS1 = 0
    mS3 = 0
    mS2 = 0
    mS1 = 0
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
            serv = G.node[inst[0]]["Service"]
            ninst = G.node[inst[0]]["Instance"]
            est = G.node[inst[0]]["EST"]
            eft = G.node[inst[linst-1]]["EFT"]
            duration = eft -est
            rstr += "\nS"+str(serv)+","+str(ninst)
            rstr += "   "+str(est)+"    "+str(eft)+"    "+str(duration)

            #fcunits = float(duration)/float(10)
            #icunits = int(math.ceil( fcunits ))
            icunits = duration
            cost = 0
            if serv == 1 :
                cost = icunits*prices[0]
                nS1 += 1
                mS1 += len(inst)
            elif serv == 2:
                cost = icunits*prices[1]
                nS2 += 1
                mS2 += len(inst)
            elif serv == 3:
                cost = icunits*prices[2]
                nS3 += 1
                mS3 += len(inst)

            total_cost += cost
            rstr += "    "+str(cost)
            tasklist = ""
            if verbose>0 :  
                for k in xrange(0,linst) :
                    if k>0 :
                        tasklist += ", "
                    tasklist += G.node[inst[k]]["name"]
            else:
                for k in xrange(0,linst) :
                    if k>0 :
                        tasklist += ", "
                    tasklist += G.node[inst[k]]["name"]
                #rstr += "    "+str(linst)              
            rstr += "    "+tasklist
        print rstr
        tot_non_inst = 0
        extra_cost = 0
        print "\ntotal instance cost: "+str(total_cost)
        if( nodes_in_inst != number_of_nodes ) :
           nonp = getNonInstanceNodes(   )
           nonstr = ""

           for j in xrange(0,number_of_nodes):
               if nonp[j]==0 :
                   nonstr += ","+G.node[j]["name"]
                   extra_cost += G.node[j]["time1"]*prices[0]
                   tot_non_inst += 1
           print "\nnon instance nodes: n="+str(tot_non_inst)+" "+nonstr[1:]+" with extra cost: "+str(extra_cost)
           total_cost += extra_cost
        tot_idle = checkIdleTime()
        if tot_idle>0:
            print "\nTotal cost: "+str(total_cost)+" for "+str(number_of_nodes),"nodes with tot idle="+str(tot_idle)
        else:
            print "\nTotal cost: "+str(total_cost)+" for "+str(number_of_nodes),"nodes"
        m1 = 0.
        m2 = 0.
        m3 = 0.
        if extra_cost>0:
          nS1 += tot_non_inst
          mS1 += tot_non_inst
        if nS1>0:
          m1 = float(mS1)/float(nS1)
        if nS2>0 :
          m2 = float(mS2)/float(nS2)
        if nS3>0:
          m3 = float(mS3)/float(nS3)
        print "\n(#,<>)","S1:("+str(nS1)+","+str(round(m1,2))+")","S2:("+str(nS2)+","+str(round(m2,2))+")","S3:("+str(nS3)+","+str(round(m3,2))+")"
        print "\n\t"+str(total_cost)+"\t"+str(G.node[number_of_nodes-1]["EFT"])+"\t("+str(nS1)+","+str(round(m1,2))+")\t("+str(nS2)+","+str(round(m2,2))+")\t("+str(nS3)+","+str(round(m3,2))+")"
    else:
        print "**** No instances found ****"

        sum_time1 = 0
        for u in G.nodes():
            sum_time1 += G.node[u]["time1"]
        total_cost = sum_time1*prices[0]


def getNonInstanceNodes(   ):
    nonp = []
    for j in xrange(0,number_of_nodes):
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

    print "Open file '",dag_file,"'"

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
              G.node[node0]["order"] = node0
              G.node[node0]["name"] = "t"+str(node0)
              G.node[node0]["time1"] = 0
              G.node[node0]["time2"] = 0
              G.node[node0]["time3"] = 0
            if not G.has_node(node1) :
              G.add_node( node1 )
              G.node[node1]['order'] = node1
              G.node[node1]["name"] = "t"+str(node1)
              G.node[node1]["time1"] = 0
              G.node[node1]["time2"] = 0
              G.node[node1]["time3"] = 0
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
        print tstr,perf_arr
        for inode in xrange(0,number_of_nodes):
           G.node[inode][tstr] = int(perf_arr[inode])
    f.close

    # two reasons for adding entry node
    # a) no entry node present
    # b) current entry node has non-zero performance
    inlist = list( G.in_degree())
    print inlist
    num_zero = 0
    for j in inlist :
      if j[1] == 0 :
        num_zero += 1
    if num_zero>1 or (num_zero == 1 and G.node[0]["time1"]>0 ):
        if num_zero>1:
            print "Add entry node to graph; dag file has no entry node"
        else:
            print "Add entry node to graph; dag file has entry node with non-zero performance"
        G1=nx.DiGraph()       
        for u in G.nodes():
            unum   = u+1
            uname  = "t"+str(unum)
            uorder = unum
            G1.add_node(unum)
            G1.node[unum]["order"] = uorder
            G1.node[unum]["name"] = uname
            G1.node[unum]["time1"] = G.node[u]["time1"]
            G1.node[unum]["time2"] = G.node[u]["time2"]
            G1.node[unum]["time3"] = G.node[u]["time3"]
        for u,v in G.edges():
            G1.add_edge( u+1, v+1 )
            G1[u+1][v+1]["throughput"] = G[u][v]["throughput"]
        print "Add entry node to graph"
        G1.add_node(0)
        G1.node[0]["order"] = 0
        G1.node[0]["name"] = "t0"
        G1.node[0]["time1"] = 0
        G1.node[0]["time2"] = 0
        G1.node[0]["time3"] = 0
        G1.node[0]["Service"] = 1
        G1.node[0]["Instance"] = -1
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
    print outlist
    num_zero = 0
    for j in outlist :
        if j[1] == 0 :
            num_zero += 1

    if num_zero>1 or (num_zero == 1 and G.node[number_of_nodes-1]["time1"]>0 ) :
        if num_zero>1:
            print "Add exit node to graph; dag file has no exit node"
        else:
            print "Add exit node to graph; dag file has exit node with non-zero performance"
        exit_node = G.number_of_nodes()
        G.add_node( exit_node  )
        G.node[exit_node]["order"] = exit_node
        G.node[exit_node]["name"] = "t"+str(exit_node)
        G.node[exit_node]["time1"] = 0
        G.node[exit_node]["time2"] = 0
        G.node[exit_node]["time3"] = 0
        G.node[exit_node]["Service"] = 1
        G.node[exit_node]["Instance"] = -1
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
    print "Mean indegree: ",str(mean_in)

    for u in G.nodes():
      G.node[u]["EST"] = -1
      G.node[u]["EFT"] = -1
      G.node[u]["LST"] = -1
      G.node[u]["LFT"] = -1
      G.node[u]["assigned"] = 0
      G.node[u]["Service"] = 1
      G.node[u]["Instance"] = -1
      G.node[u]["time"] = G.node[u]["time1"]

    #check entry node and exit node
    if( G.node[0]["time1"]==0 and G.node[0]["time2"]==0 and G.node[0]["time3"]==0 ):
         G.node[0]["time"]=0
         G.node[0]["assigned"]=1
    if( G.node[number_of_nodes-1]["time1"]==0 and G.node[number_of_nodes-1]["time2"]==0 and G.node[number_of_nodes-1]["time3"]==0 ):
         G.node[number_of_nodes-1]["time"]=0
         G.node[number_of_nodes-1]["assigned"]=1

    deadline = 0

    if options.json == 1 :
        dumpJSON(0,number_of_nodes-1)

    f = open(deadline_file, 'r') 
    for line in f:
        line = line.strip(' ')
        line = line.rstrip('\n')
        line = line.rstrip('\r')
        deadline = int(line)
    f.close
    print "deadline: ",deadline

    prices = []
    f = open(price_file, 'r') 
    for line in f:
        line = line.strip(' ')
        line = line.rstrip('\n')
        line = line.rstrip('\r')
        price_arr = line.split(',')
        for pr in price_arr :
          prices.append(int(pr))
    f.close
    print "prices: ",prices

    printPerformances()

    sum_time1 = 0
    sum_time2 = 0
    sum_time3 = 0
    for u in G.nodes():
      sum_time1 += G.node[u]["time1"]
      sum_time2 += G.node[u]["time2"]
      sum_time3 += G.node[u]["time3"]
    print "sum time1: ",str(sum_time1)
    print "sum time2: ",str(sum_time2)
    print "sum time3: ",str(sum_time3)

    G.node[0]["EST"] = 0
    G.node[0]["EFT"] = 0 + G.node[0]["time1"]
    G.node[0]["assigned"] = 1
    G.node[0]["Service"] = 1
    graphAssignEST( number_of_nodes-1 )

    G.node[(number_of_nodes-1)]["LFT"] = deadline
    G.node[(number_of_nodes-1)]["LST"] = deadline - G.node[(number_of_nodes-1)]["time1"]
    G.node[(number_of_nodes-1)]["assigned"] = 1
    G.node[(number_of_nodes-1)]["Service"] = 1
    graphAssignLFT( 0 )

    #printGraphTimes( )

    pcp = getCriticalPath( number_of_nodes-1 )
    if len(pcp) ==  0:
        sys.exit("\nERROR **** No critical path found ****\n")

    criticali_time1 = 0
    criticali_time2 = 0
    criticali_time3 = 0
    criticalp_time1 = 0
    criticalp_time2 = 0
    criticalp_time3 = 0
    tot_indegree = 0
    for j in xrange(0,len(pcp)-1):
        tot_indegree += G.in_degree(pcp[j])
        criticali_time1 += G.node[pcp[j]]["time1"]
        criticali_time2 += G.node[pcp[j]]["time2"]
        criticali_time3 += G.node[pcp[j]]["time3"]
        throughput = G[pcp[j]][pcp[j+1]]["throughput"]
        criticalp_time1 += G.node[pcp[j]]["time1"] + throughput
        criticalp_time2 += G.node[pcp[j]]["time2"] + throughput
        criticalp_time3 += G.node[pcp[j]]["time3"] + throughput

    tot_indegree += G.in_degree(pcp[len(pcp)-1])
    criticali_time1 += G.node[pcp[len(pcp)-1]]["time1"]
    criticali_time2 += G.node[pcp[len(pcp)-1]]["time2"]
    criticali_time3 += G.node[pcp[len(pcp)-1]]["time3"]
    criticalp_time1 += G.node[pcp[len(pcp)-1]]["time1"]
    criticalp_time2 += G.node[pcp[len(pcp)-1]]["time2"]
    criticalp_time3 += G.node[pcp[len(pcp)-1]]["time3"]
    
    if options.perc>0 :
      deadline = int(100.*float(criticalp_time1)/float(options.perc))
      print "new deadline: ",deadline

    G.node[0]["EST"] = 0
    G.node[0]["EFT"] = 0 + G.node[0]["time1"]
    graphAssignEST( number_of_nodes-1 )

    G.node[(number_of_nodes-1)]["LFT"] = deadline
    G.node[(number_of_nodes-1)]["LST"] = deadline - G.node[(number_of_nodes-1)]["time1"]
    graphAssignLFT( 0 )

    print "\nStart situation"
    printGraphTimes( )

    critper1 = 100.0*float(criticalp_time1)/float(deadline)
    critper2 = 100.0*float(criticalp_time2)/float(deadline)
    critper3 = 100.0*float(criticalp_time3)/float(deadline)
    critreduc1 = 100.0*float(criticali_time1)/float(deadline)
    critreduc2 = 100.0*float(criticali_time2)/float(deadline)
    critreduc3 = 100.0*float(criticali_time3)/float(deadline)
    mean_indegree = float(tot_indegree)/float(len(pcp))
    print "critical path: ",pcp," mean_indegree:"+str(round(mean_indegree,2))
    print "criticalp_time(S1)="+str(criticalp_time1)+" is "+str(round(critper1,2))+"% of deadline("+str(deadline)+")"
    print "criticalp_time(S2)="+str(criticalp_time2)+" is "+str(round(critper2,2))+"% of deadline("+str(deadline)+")"
    print "criticalp_time(S3)="+str(criticalp_time3)+" is "+str(round(critper3,2))+"% of deadline("+str(deadline)+")"
    print "criticali_time(S1)="+str(criticali_time1)+" is "+str(round(critreduc1,2))+"% of deadline("+str(deadline)+")"
    print "criticali_time(S2)="+str(criticali_time2)+" is "+str(round(critreduc2,2))+"% of deadline("+str(deadline)+")"
    print "criticali_time(S3)="+str(criticali_time3)+" is "+str(round(critreduc3,2))+"% of deadline("+str(deadline)+")"

    start_str = "start configuartion: cost="+str(sum_time1*prices[0])+"  EFT(exit)="+str(G.node[(number_of_nodes-1)]["EFT"])
    critical_str = str(deadline)+"\t"+str(round(critper1,2))+"("+str(round(critreduc1,2))+")%"
    critical_str += "\t"+str(round(critper2,2))+"("+str(round(critreduc2,2))+")%"
    critical_str += "\t"+str(round(critper3,2))+"("+str(round(critreduc3,2))+")%"

    assignParents( number_of_nodes-1 )
    print "\nEnd situation"
    printGraphTimes( )
  
    # entry and exit node not part of PCP, so
    # adjust LST, LFT of entry node
    # adjust EST, EFT of exit node
    updateNode(0)
    updateNode(number_of_nodes-1)

    # check PCP end situation

    retVal = checkGraphTimes()
    print "checkGraphTimes: retVal="+str(retVal)
    
    if retVal<0 :
       print "\n**** Try correction sweep ****"

       updateGraphTimes()
       retVal = checkGraphTimes()
       if retVal<0 :
          print "\n**** No valid solution found after correction sweep ****"
       else:
          print "\n**** Correction sweep successful ****"

    if retVal == -1 :
        print "\nFinal situation"

        printGraphTimes()

        print "\n"+start_str
        print "\n**** Invalid final configuration ****"
    else:

       tot_idle = checkIdleTime()
       if tot_idle>0:
            print "\n**** Try to split instances with idle time ****"
            splitInstances()
            updateGraphTimes()
            printGraphTimes( )
            retval = checkGraphTimes()
            if retVal<0 :
                print "\n**** Split failed ****"
            else:
                print "\n**** Split successful ****"
       if retVal == -1 :
           print "\nFinal situation"

           printGraphTimes()

           print "\n"+start_str
           print "\n**** Invalid final configuration ****"
       else:
          checkIdleTime()
          printResult()
          print "\n"+start_str
          print "final configuration:",critical_str
          print "final configuration: cost="+str(total_cost)+"  EFT(exit)="+str(G.node[(number_of_nodes-1)]["EFT"])
#############################
# The program starts here...
#############################
if __name__ == '__main__':
         
     main(sys.argv[1:])
        
#############################
# end of the program
#############################
    
