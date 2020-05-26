#!/usr/bin/env python3


import sys
import os.path
from libsbml import readSBML
import rpSBML
import tempfile
import tarfile
import glob
from shutil import copy2
import argparse


# Python code t get difference of two lists
# Using set()
def Diff(li1, li2):
    return (list(set(li1) - set(li2)))

PRINT = False



def main (args):
    """Usage: -inputTar rpUnicity input.tar -outputTar output.tar
    """

    parser = argparse.ArgumentParser('Python wrapper to parse rpUnicity to generate an archive containing unique pathways collection')
    parser.add_argument('-inputTar', type=str)
    parser.add_argument('-outputTar', type=str)
    params = parser.parse_args()

    # if len(args) != 3:
    #    print("\n" + "Usage: rpUnicity -inputTar input.tar -outputTar output.tar" + "\n")
    #    return 1
    #
    # inputTar = args[1]
    # outputTar = args[2]

    deduplicate(params.inputTar, params.outputTar)


def deduplicate(inputTar, outputTar):

    files = []

    with tempfile.TemporaryDirectory() as tmpOutputFolder:
        with tempfile.TemporaryDirectory() as tmpInputFolder:

            tar = tarfile.open(inputTar, mode='r')
            tar.extractall(path=tmpInputFolder)
            tar.close()

            detect_and_copy_unique_pathways(tmpInputFolder, tmpOutputFolder)

            with tarfile.open(outputTar, "w:gz") as tar:
                tar.add(tmpOutputFolder, arcname=os.path.sep)

            # with tarfile.open(fileobj=outputTar, mode='w:xz') as ot:
            #     for file in glob.glob(tmpOutputFolder+'/*'):
            #         info = tarfile.TarInfo(file)
            #         info.size = os.path.getsize(file)
            #         print(file, info)
            #         ot.addfile(tarinfo=info, fileobj=open(file, 'rb'))

    return 0


def detect_and_copy_unique_pathways(tmpInputFolder, tmpOutputFolder):
    unique_files = list_unique_pathways(glob.glob(tmpInputFolder+'/*'))
    for file in unique_files:
        copy2(file, tmpOutputFolder)

def search_key(keys, dict):
    for key in keys:
        if key in dict:
            return key

def list_unique_pathways(files):

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
        # Pathways dict
        d_reactions = {}

        keys = ['inchikey', 'inchi', 'smiles']
        # Select Reactions already loaded (w/o Sink one then)
        for reaction in reactions:

            d_reactions[reactions[reaction]['smiles']] = {}

            # Fill the reactants in a dedicated dict
            d_reactants = {}
            for reactant in model.getReaction(reaction).getListOfReactants():#inchikey / inchi sinon miriam sinon IDs
                # Il faut enregistrer toutes les infos (inchi, smiles, id)
                key = search_key(keys, species[reactant.getSpecies()])
                if key: key = species[reactant.getSpecies()][key]
                else:
                    key = reactant.getSpecies()
                d_reactants[key] = reactant.getStoichiometry()
            # Put all reactants dicts in reactions dict for which smiles notations are the keys
            d_reactions[reactions[reaction]['smiles']]['Reactants'] = d_reactants

            # Fill the products in a dedicated dict
            d_products = {}
            for product in model.getReaction(reaction).getListOfProducts():
                key = search_key(keys, species[product.getSpecies()])
                if key: key = species[product.getSpecies()][key]
                else:
                    key = product.getSpecies()
                d_products[key] = product.getStoichiometry()
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




    return unique_files



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
