class ffrgs:

    def __init__(self, version, genome, author):
    #def __init__(self, version, genome, author, assembler, place, taxa, assemblySoftware, physicalSample, dateCreated, scholarlyArticle, documentation):
        self.version = version
        self.genome = genome
        self.author = author
        #self.assembler = assembler
        #self.place = place
        #self.taxa = taxa
        #self.assemblySoftware = assemblySoftware
        #self.physicalSample = physicalSample
        #self.dateCreated = dateCreated
        #self.instrument = []
        #self.scholarlyArticle = scholarlyArticle
        #self.documentation = documentation
        #self.identifier = []
        #self.relatedLink = []

    def __repr__(self):
        return f'ffrgs("{self.version},{self.genome},{self.author}")'

    def __str__(self):
        return f'("{self.version},{self.genome},{self.author}")'
