from pydantic import BaseModel


class SimilarDoc(BaseModel):
    document_id: str
    title: str
    category: str | None
    department: str | None
    similarity: float
    matched_page: int | None
    snippet: str


class SimilarResponse(BaseModel):
    document: dict
    similar: list[SimilarDoc]


class ClusterMember(BaseModel):
    id: str
    title: str
    category: str | None


class Cluster(BaseModel):
    cluster_id: int
    num_documents: int
    dominant_terms: list[str]
    documents: list[ClusterMember]


class ClustersResponse(BaseModel):
    clusters: list[Cluster]
    k: int | None = None
    docs_considered: int | None = None
    note: str | None = None
