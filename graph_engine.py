"""
Graph Engine - Builds and queries the business data graph
"""

import json
import networkx as nx
from pathlib import Path
from collections import defaultdict


class GraphEngine:
    """Manages the business data graph"""
    
    def __init__(self, data_directory):
        self.data_dir = Path(data_directory)
        self.graph = nx.MultiDiGraph()
        self.entities = defaultdict(dict)
        
    def load_jsonl_file(self, filepath):
        """Load records from JSONL file"""
        records = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except:
                        continue
        return records
    
    def identify_entity_type(self, record):
        """Determine entity type from record fields"""
        fields = set(record.keys())
        
        if 'billingDocument' in fields and 'billingDocumentType' in fields:
            return 'billing_doc'
        elif 'billingDocument' in fields and 'billingDocumentItem' in fields:
            return 'billing_item'
        elif 'salesOrder' in fields and 'salesOrderItem' in fields:
            return 'sales_order'
        elif 'deliveryDocument' in fields and 'deliveryDocumentItem' in fields:
            return 'delivery'
        elif 'product' in fields and 'productType' in fields:
            return 'product'
        elif 'businessPartner' in fields and 'addressId' in fields:
            return 'address'
        
        return None
    
    def add_billing_docs(self, records):
        """Add billing document nodes"""
        for rec in records:
            node_id = f"BD_{rec['billingDocument']}"
            self.graph.add_node(node_id, entity_type='billing_doc', **rec)
            self.entities['billing_doc'][node_id] = rec
            
            # Link to customer
            if rec.get('soldToParty'):
                customer_id = f"CUST_{rec['soldToParty']}"
                self.graph.add_edge(node_id, customer_id, rel_type='billed_to')
    
    def add_billing_items(self, records):
        """Add billing item nodes and relationships"""
        for rec in records:
            item_id = f"BI_{rec['billingDocument']}_{rec['billingDocumentItem']}"
            self.graph.add_node(item_id, entity_type='billing_item', **rec)
            self.entities['billing_item'][item_id] = rec
            
            # Link to parent billing document
            doc_id = f"BD_{rec['billingDocument']}"
            self.graph.add_edge(doc_id, item_id, rel_type='has_item')
            
            # Link to product
            if rec.get('material'):
                product_id = f"PROD_{rec['material']}"
                self.graph.add_edge(item_id, product_id, rel_type='for_product')
            
            # Link to sales order
            if rec.get('referenceSdDocument'):
                so_id = f"SO_{rec['referenceSdDocument']}_{rec.get('referenceSdDocumentItem', '10')}"
                self.graph.add_edge(item_id, so_id, rel_type='refs_sales_order')
    
    def add_sales_orders(self, records):
        """Add sales order nodes"""
        for rec in records:
            so_id = f"SO_{rec['salesOrder']}_{rec.get('salesOrderItem', '10')}"
            self.graph.add_node(so_id, entity_type='sales_order', **rec)
            self.entities['sales_order'][so_id] = rec
    
    def add_deliveries(self, records):
        """Add delivery nodes and relationships"""
        for rec in records:
            del_id = f"DEL_{rec['deliveryDocument']}_{rec['deliveryDocumentItem']}"
            self.graph.add_node(del_id, entity_type='delivery', **rec)
            self.entities['delivery'][del_id] = rec
            
            # Link to sales order
            if rec.get('referenceSdDocument'):
                so_id = f"SO_{rec['referenceSdDocument']}_{rec.get('referenceSdDocumentItem', '10')}"
                self.graph.add_edge(del_id, so_id, rel_type='fulfills_order')
            
            # Link to plant
            if rec.get('plant'):
                plant_id = f"PLANT_{rec['plant']}"
                self.graph.add_edge(del_id, plant_id, rel_type='from_plant')
    
    def add_products(self, records):
        """Add product nodes"""
        for rec in records:
            product_id = f"PROD_{rec['product']}"
            self.graph.add_node(product_id, entity_type='product', **rec)
            self.entities['product'][product_id] = rec
    
    def add_addresses(self, records):
        """Add address nodes"""
        for rec in records:
            if rec.get('businessPartner'):
                customer_id = f"CUST_{rec['businessPartner']}"
                addr_id = f"ADDR_{rec['businessPartner']}_{rec.get('addressId', '1')}"
                self.graph.add_node(addr_id, entity_type='address', **rec)
                self.entities['address'][addr_id] = rec
                self.graph.add_edge(customer_id, addr_id, rel_type='has_address')
    
    def build_graph(self):
        """Process all data files and build the graph"""
        print("Building graph from data files...")
        
        processors = {
            'billing_doc': self.add_billing_docs,
            'billing_item': self.add_billing_items,
            'sales_order': self.add_sales_orders,
            'delivery': self.add_deliveries,
            'product': self.add_products,
            'address': self.add_addresses
        }
        
        for filepath in self.data_dir.glob('*.jsonl'):
            records = self.load_jsonl_file(filepath)
            if not records:
                continue
                
            entity_type = self.identify_entity_type(records[0])
            if entity_type in processors:
                processors[entity_type](records)
        
        print(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        return self.graph
    
    def get_summary(self):
        """Get graph statistics"""
        entity_counts = defaultdict(int)
        for node, data in self.graph.nodes(data=True):
            entity_counts[data.get('entity_type', 'unknown')] += 1
        
        rel_counts = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            rel_counts[data.get('rel_type', 'unknown')] += 1
        
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'entities': dict(entity_counts),
            'relationships': dict(rel_counts)
        }
    
    def export_for_viz(self, max_nodes=500):
        """Export graph for frontend visualization"""
        nodes = []
        edges = []
        
        all_nodes = list(self.graph.nodes(data=True))
        if len(all_nodes) > max_nodes:
            import random
            sampled = random.sample(all_nodes, max_nodes)
            sampled_ids = {n[0] for n in sampled}
        else:
            sampled = all_nodes
            sampled_ids = {n[0] for n in sampled}
        
        for node_id, data in sampled:
            nodes.append({
                'data': {
                    'id': node_id,
                    'label': node_id.split('_', 1)[1] if '_' in node_id else node_id,
                    'type': data.get('entity_type', 'unknown')
                }
            })
        
        for u, v, data in self.graph.edges(data=True):
            if u in sampled_ids and v in sampled_ids:
                edges.append({
                    'data': {
                        'source': u,
                        'target': v,
                        'relationship': data.get('rel_type', 'related')
                    }
                })
        
        return {'nodes': nodes, 'edges': edges}


if __name__ == '__main__':
    engine = GraphEngine('data')
    engine.build_graph()
    print(engine.get_summary())
