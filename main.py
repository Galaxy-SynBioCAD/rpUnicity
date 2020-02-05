#!/usr/bin/env python3


import sys
import os.path
from libsbml import readSBML
import rpSBML


# Python code t get difference of two lists
# Using set()
def Diff(li1, li2):
    return (list(set(li1) - set(li2)))

PRINT = False



def main (args):
    """Usage: rpUnicity <dirname>
    """


    if len(args) != 2:
       print("\n" + "Usage: rpUnicity <dirname>" + "\n")
       return 1

    path = args[1]
    files = []

    # for f_or_d in os.listdir(path):
    #     if os.path.isfile(f_or_d) and '.xml' in f_or_d:
    #         files.append(os.path.join(r, file))

    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if '.xml' in file:
                files.append(os.path.join(r, file))

    d_pathways = {}

    for filename in files:

        document = readSBML(filename)

        if document.getNumErrors() > 0:
           printLine("Encountered the following SBML errors:" )
           document.printErrors()
           return 1

        level = document.getLevel()
        version = document.getVersion()

        model = document.getModel()

        if model is None:
           print("No model present." )
           return 1

        idString = "  id: "
        if level == 1:
         idString = "name: "
        id = "(empty)"
        if model.isSetId():
         id = model.getId()

         if PRINT:
             PrintInfos1(filename, level, version, idString, id, model)

        # Read RP Annotations
        groups = model.getPlugin('groups')
        rpsbml = rpSBML.rpSBML('test')


        # Get Reactions
        reactions = {}
        for member in groups.getGroup('rp_pathway').getListOfMembers():
            object = model.getReaction(member.getIdRef())
            reactions[member.getIdRef()] = rpsbml.readBRSYNTHAnnotation(object.getAnnotation())


        # Get Species
        species = {}
        for specie in model.getListOfSpecies():
            species[specie.getId()] = rpsbml.readBRSYNTHAnnotation(specie.getAnnotation())

        # print()
        # print("REACTIONS")
        # print(reactions)
        # print()
        # print("SPECIES")
        # print(species)
        # print()

        # Pathways dict
        d_reactions = {}

        # Select Reactions already loaded (w/o Sink one then)
        for reaction in reactions:

            d_reactions[reactions[reaction]['smiles']] = {}

            # Fill the reactants in a dedicated dict
            d_reactants = {}
            for reactant in model.getReaction(reaction).getListOfReactants():#inchikey / inchi sinon miriam sinon IDs
                # Il faut enregistrer toutes les infos (inchi, miriam, ids)
                d_reactants[species[reactant.getSpecies()]['inchikey']] = reactant.getStoichiometry()
            # Put all reactants dicts in reactions dict for which smiles notations are the keys
            d_reactions[reactions[reaction]['smiles']]['Reactants'] = d_reactants

            # Fill the products in a dedicated dict
            d_products = {}
            for product in model.getReaction(reaction).getListOfProducts():
                d_products[species[product.getSpecies()]['inchikey']] = product.getStoichiometry()
            # Put all products dicts in reactions dict for which smiles notations are the keys
            d_reactions[reactions[reaction]['smiles']]['Products'] = d_products

            d_pathways[filename] = d_reactions

            if PRINT:
                PrintInfos2(reaction, d_reactions)

    unique_pathways = []
    unique_files = []

    for file,pathway in d_pathways.items():
        if pathway not in unique_pathways:
            unique_pathways += [pathway]
            unique_files += [file]

    # print(files)
    # print()
    print(unique_files)
    # print()
    # print(Diff(files,unique_files))


    return 0


def PrintInfos1(filename, level, version, idString, id, model):
    print("\n"
    + "File: " + filename
    + " (Level " + str(level) + ", version " + str(version) + ")" )

    print("               "
    + idString
    + id )

    if model.isSetSBOTerm():
        print("      model sboTerm: " + model.getSBOTerm() )

        print("functionDefinitions: " + str(model.getNumFunctionDefinitions()) )
        print("    unitDefinitions: " + str(model.getNumUnitDefinitions()) )
        print("   compartmentTypes: " + str(model.getNumCompartmentTypes()) )
        print("        specieTypes: " + str(model.getNumSpeciesTypes()) )
        print("       compartments: " + str(model.getNumCompartments()) )
        print("            species: " + str(model.getNumSpecies()) )
        print("         parameters: " + str(model.getNumParameters()) )
        print(" initialAssignments: " + str(model.getNumInitialAssignments()) )
        print("              rules: " + str(model.getNumRules()) )
        print("        constraints: " + str(model.getNumConstraints()) )
        print("          reactions: " + str(model.getNumReactions()) )
        print("             events: " + str(model.getNumEvents()) )
        print("\n")

def PrintInfos2(reac_name, reaction):
    print('\033[1m' + reac_name + '\033[0m')
    print(reaction)
    print()


if __name__ == '__main__':
    main(sys.argv)
