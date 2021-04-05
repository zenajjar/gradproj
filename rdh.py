import original_embed
import original_extract
import scaling_embed
import scaling_extract
from unidirection import uni_embed, bp_uni_embed, uni_extract


class RDH:
    INF = 10000

    def __init__(self, label, limit, embed, extract=None):
        self.embed = embed
        self.extract = extract
        self.label = label
        if limit == -1:
            self.limit = RDH.INF
        else:
            self.limit = limit

    def __str__(self) -> str:
        return self.label


original_algorithm = RDH('original', 64, original_embed.embed, original_extract.extract)
scaling_algorithm = RDH('scaling', -1, scaling_embed.embed, scaling_extract.extract)
unidirectional_algorithm = RDH('unidirectional', -1, uni_embed.embed, uni_extract.extract)
bp_unidirectional_algorithm = RDH('bp_unidirectional', -1, bp_uni_embed.embed, uni_extract.extract)
