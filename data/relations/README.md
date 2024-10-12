# CAIDA

Founded in 1997, the [Center for Applied Internet Data Analysis (CAIDA)][1] conducts network research and builds research infrastructure to support large-scale data collection, curation, and data distribution to the scientific research community. CAIDA is based at the San Diego Supercomputer Center, located on the UC San Diego campus in La Jolla, CA.


## 20201201.as-rel and 20201201.ppdc-ases

Contains AS relationships inferred using the method
described in [AS Relationships, Customer Cones, and Validation, IMC'13][2].

The as-rel files contain p2p and p2c relationships.  The format is:

	<provider-as>|<customer-as>|-1
	<peer-as>|<peer-as>|0

The ppdc-ases files contain the provider-peer customer cones inferred for
each AS.  Each line specifies an AS and all ASes we infer to be reachable
following a customer link.  The format is:

	<cone-as> <customer-1-as> <customer-2-as> .. <customer-N-as>


## 20201201.as-rel2

Contains AS relationships that combine the '20201201.as-rel' AS relationships inferred using the method described in [AS Relationships, Customer Cones, and Validation, IMC'13][2],
with AS relationships inferred from [Ark traceroutes, and from multilateral peering][3].
 
To do this we first infer which AS owns each router independent of the
interface addresses observed at that router. The ownership inferences
are based on IP-to-AS mapping derived from public BGP data, list of
peering prefixes from PeeringDB, and the previously inferred business AS
relationships. Then we convert the observed IP path into an AS path
using the router ownership information (rather than mapping each
observed IP to AS directly) and retain the first AS link in the
resulting path for the AS graph.
 
The as-rel files contain p2p and p2c relationships.  The format is:

	<provider-as>|<customer-as>|-1
	<peer-as>|<peer-as>|0|<source>


## Additional Information

Caida relationship files from 2020: 02 and 03 were not avaliable, so we copy the 01 twice.


[1]: https://www.caida.org/home/ "Center for Applied Internet Data Analysis - CAIDA"
[2]: http://www.caida.org/publications/papers/2013/asrank/ "AS Relationships, Customer Cones, and Validation, IMC'13"
[3]: http://www.caida.org/publications/papers/2013/inferring_multilateral_peering/ "Ark traceroutes, and from
multilateral peering"
