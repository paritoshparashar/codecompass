from enum import Enum, auto


class IssueType (Enum) : 
    BUG = auto()
    FEATURE = auto()
    DOCS = auto()
    PERFORMANCE = auto()
    TEST_GAP = auto()

class Regime (Enum) : 
    SYMPTOM = auto() # the issue is explained vagualy - just explains the symptom
    MECHANISM = auto() # the issue is explained mechanistically - explains the underlying mechanism of the issue


'''
An edge type is justified when it supports at least one important operation, such as:
- retrieving related code
- expanding candidates during localization
- calculating graph centrality
- explaining why a location was recommended
- ranking likely issue locations
.. "extension possible"
'''
# Define the Edge types of the repository graph (EdgeType.length many graphs are constructed for each repository)
class EdgeType (Enum) :
    IMPORTS = auto() # the edge represents an import statement
    CALLS = auto() # tracing execution path - the edge represents a function call
    INHERITS = auto() # understanding behaviour distribution
    CONTAINS = auto() # connect the hierarchy inside a file [file -> class -> method -> statement]


'''Still not completed yet'''
# Pipelines accept different types of evidence to support their analysis.
class EvidenceTypes (Enum) :
    TRACEBACK = auto()  # evidence for a bug pipeline
    TRACEDIFF = auto() # evidence for a bug pipeline
    MUTANTDIFF = auto() # evidence for a testgap pipeline
