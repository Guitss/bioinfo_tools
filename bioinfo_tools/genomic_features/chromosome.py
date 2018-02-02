from pprint import pprint
from Bio.SeqFeature import FeatureLocation
from bioinfo_tools.genomic_features.gene import Gene


class Chromosome(object):
    def __init__(self, chromosome_id, assembly_name = None):
        self.chromosome_id = chromosome_id
        self.assembly_name = assembly_name
        self.length = 0
        self._genes = {}
        self._index_by_position = dict()
    
    def __repr__(self):
        return u"%s (%s genes)" % (self.chromosome_id, len(self.genes))
    
    def add_gene(self, gff_feature, lookup_attributes = ('gene_id', 'Name', 'ID', 'id')):
        """
        :param gff_feature: dictionnary of various gff features
        :type gff_feature: dict
        
        :param lookup_attributes: potential attribute names hosting the gene ID
        :type lookup_attributes: tuple
        
        :return: created gene object
        :rtype: Gene
        """
        gene_id = None
        
        if 'gene_id' in gff_feature:
            gene_id = gff_feature.pop('gene_id')
        elif 'attributes' in gff_feature:
            for attribute in lookup_attributes:
                if attribute in gff_feature['attributes'] and gff_feature['attributes'][attribute].rstrip():
                    gene_id = gff_feature['attributes'][attribute]
                    break
        
        if not gene_id:
            pprint(gff_feature)
            raise Exception("gene_id not found in given GFF feature")
        
        # remove all potential duplicated keys
        for key_name in ('chromosome', 'start', 'end', 'strand', 'assembly_name', 'gene_id'):
            gff_feature.get('attributes', {}).pop(key_name, None)
        
        gene = Gene(
            gene_id = gene_id,
            chromosome = self,
            start = gff_feature.get('start', 0),
            end = gff_feature.get('end', 0),
            strand = gff_feature.get('strand', None),
            assembly_name = self.assembly_name,
            **gff_feature.get('attributes', {})
        )
        for feature_type in ('mRNA', 'RNA', 'transcript'):
            for transcript in gff_feature.get(feature_type, gff_feature.get(feature_type.lower(), gff_feature.get(feature_type.upper(), []))):
                gene.add_transcript(transcript)
        
        self._genes[gene['gene_id']] = gene
        self._add_gene_to_index(gene)
        return gene
    
    @property
    def genes(self):
        """
        :rtype: List[Gene]
        """
        return list(self._genes.values())
    
    @property
    def sorted_genes(self):
        """
        :rtype: List[Gene]
        """
        if not hasattr(self, "_sorted_genes"):
            self._sorted_genes = sorted(self._genes.values(), key = lambda gene: gene.location.start)
        return self._sorted_genes
    
    def get_genes_at(self, position):
        """
        :rtype: List[Gene]
        """
        if not self._index_by_position:
            self.build_index()
        found_genes = list()
        for interval, gene in self._index_by_position.items():
            if position in interval and gene not in found_genes:
                found_genes.append(gene)
        return found_genes
    
    def get_gene(self, gene_id):
        """
        :param gene_id: some gene ID
        :type gene_id: str
        :rtype: Gene
        """
        return self._genes.get(gene_id, None)

    def build_index(self):
        self._index_by_position = dict()
        for gene in self.genes:
            self._add_gene_to_index(gene)
    
    def _add_gene_to_index(self, gene):
        """
        :param gene: a Gene object
        :type gene: Gene
        """
        if not hasattr(self, "_index_by_position"):
            self._index_by_position = dict()
        self._index_by_position[range(gene.location.start, gene.location.end + 1)] = gene

    def attach_nucleic_sequence(self, sequence):
        self.nucleic_sequence = sequence
        self.length = len(sequence)
    
    def extract_sequence(self, start, end):
        location = FeatureLocation(start, end)
        return location.extract(self.nucleic_sequence)
