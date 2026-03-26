"""
Query Processor - Handles natural language queries
"""

import os
import re
from collections import defaultdict
from groq import Groq


class QueryProcessor:
    """Processes natural language queries against the graph"""
    
    def __init__(self, graph_engine):
        self.engine = graph_engine
        self.groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY', ''))
        
    def classify_query(self, query):
        """Determine query type"""
        q = query.lower()
        
        # Product analysis
        if ('product' in q or 'material' in q) and any(w in q for w in ['most', 'top', 'highest']):
            return 'product_count'
        
        # Trace document
        if 'trace' in q or 'flow' in q:
            doc_match = re.search(r'\b\d{8}\b', query)
            if doc_match:
                return ('trace_doc', doc_match.group())
        
        # Incomplete flows
        if ('delivered' in q and 'not' in q and 'billed' in q) or 'incomplete' in q:
            return 'incomplete_flows'
        
        # Summary stats
        if 'how many' in q or 'count' in q or 'total' in q:
            return 'summary'
        
        return 'general'
    
    def is_off_topic(self, query):
        """Check if query is off-topic"""
        off_topic_patterns = [
            r'write.*(poem|story|essay)',
            r'(weather|news|sports)',
            r'(cook|recipe)',
            r'meaning of life'
        ]
        
        q = query.lower()
        return any(re.search(p, q) for p in off_topic_patterns)
    
    def execute_product_count(self):
        """Find products with most billing documents"""
        counts = defaultdict(int)
        
        for node_id, data in self.engine.graph.nodes(data=True):
            if data.get('entity_type') == 'billing_item':
                product = data.get('material', '')
                if product:
                    counts[product] += 1
        
        top_5 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        result = "**Top 5 Products by Billing Documents:**\n\n"
        for i, (product, count) in enumerate(top_5, 1):
            result += f"{i}. `{product}`: **{count}** billing documents\n"
        
        return result
    
    def execute_trace_doc(self, doc_id):
        """Trace flow of a billing document"""
        node_id = f"BD_{doc_id}"
        
        if node_id not in self.engine.graph:
            return f"❌ Billing document `{doc_id}` not found in dataset."
        
        result = []
        result.append(f"**📄 Billing Document {doc_id}**\n")
        
        # Get document details
        doc_data = self.engine.graph.nodes[node_id]
        result.append(f"- Amount: `{doc_data.get('totalNetAmount', 'N/A')} {doc_data.get('transactionCurrency', '')}`")
        result.append(f"- Date: `{doc_data.get('billingDocumentDate', 'N/A')[:10]}`")
        if doc_data.get('soldToParty'):
            result.append(f"- Customer: `{doc_data['soldToParty']}`")
        
        # Get items
        items = [n for n in self.engine.graph.successors(node_id) 
                if self.engine.graph.nodes[n].get('entity_type') == 'billing_item']
        
        result.append(f"\n**📦 Line Items ({len(items)}):**\n")
        
        for item_id in items[:5]:
            item_data = self.engine.graph.nodes[item_id]
            result.append(f"- Product: `{item_data.get('material', 'N/A')}`")
            result.append(f"  - Quantity: `{item_data.get('billingQuantity', 'N/A')} {item_data.get('billingQuantityUnit', '')}`")
            result.append(f"  - Amount: `{item_data.get('netAmount', 'N/A')} {item_data.get('transactionCurrency', '')}`")
            
            # Find sales order
            for neighbor in self.engine.graph.successors(item_id):
                if self.engine.graph.nodes[neighbor].get('entity_type') == 'sales_order':
                    result.append(f"  - Sales Order: `{neighbor}`")
                    
                    # Find delivery
                    for pred in self.engine.graph.predecessors(neighbor):
                        if self.engine.graph.nodes[pred].get('entity_type') == 'delivery':
                            del_data = self.engine.graph.nodes[pred]
                            result.append(f"    - Delivery: `{pred}` from Plant `{del_data.get('plant', 'N/A')}`")
            
            result.append("")
        
        if len(items) > 5:
            result.append(f"_... and {len(items) - 5} more items_")
        
        return "\n".join(result)
    
    def execute_incomplete_flows(self):
        """Find sales orders delivered but not billed"""
        # Find sales orders with deliveries
        delivered = set()
        for node_id, data in self.engine.graph.nodes(data=True):
            if data.get('entity_type') == 'delivery':
                for neighbor in self.engine.graph.successors(node_id):
                    if self.engine.graph.nodes[neighbor].get('entity_type') == 'sales_order':
                        delivered.add(neighbor)
        
        # Find sales orders with billing
        billed = set()
        for node_id, data in self.engine.graph.nodes(data=True):
            if data.get('entity_type') == 'billing_item':
                for neighbor in self.engine.graph.successors(node_id):
                    if self.engine.graph.nodes[neighbor].get('entity_type') == 'sales_order':
                        billed.add(neighbor)
        
        # Find incomplete
        incomplete = delivered - billed
        
        if not incomplete:
            return "✅ **All delivered sales orders have corresponding billing documents.**"
        
        result = [f"**⚠️ Found {len(incomplete)} sales orders delivered but NOT billed:**\n"]
        
        for i, so_id in enumerate(list(incomplete)[:10], 1):
            so_data = self.engine.graph.nodes[so_id]
            result.append(f"{i}. `{so_id}`")
            result.append(f"   - Delivery date: `{so_data.get('confirmedDeliveryDate', 'N/A')}`")
        
        if len(incomplete) > 10:
            result.append(f"\n_... and {len(incomplete) - 10} more_")
        
        return "\n".join(result)
    
    def execute_summary(self):
        """Get summary statistics"""
        summary = self.engine.get_summary()
        
        result = ["**📊 Dataset Summary**\n"]
        result.append(f"- Total Nodes: **{summary['total_nodes']}**")
        result.append(f"- Total Edges: **{summary['total_edges']}**")
        result.append("\n**Entities:**")
        for entity, count in summary['entities'].items():
            result.append(f"- {entity}: {count}")
        
        return "\n".join(result)
    
    def process(self, query):
        """Main query processing entry point"""
        # Check off-topic
        if self.is_off_topic(query):
            return {
                'answer': "🚫 This system is designed to answer questions related to the provided dataset only.",
                'success': True
            }
        
        # Classify and execute
        classification = self.classify_query(query)
        
        try:
            if classification == 'product_count':
                answer = self.execute_product_count()
            elif isinstance(classification, tuple) and classification[0] == 'trace_doc':
                answer = self.execute_trace_doc(classification[1])
            elif classification == 'incomplete_flows':
                answer = self.execute_incomplete_flows()
            elif classification == 'summary':
                answer = self.execute_summary()
            else:
                # Fallback to LLM explanation
                answer = self.llm_fallback(query)
            
            return {'answer': answer, 'success': True}
            
        except Exception as e:
            return {'answer': f"❌ Error: {str(e)}", 'success': False}
    
    def llm_fallback(self, query):
        """Use LLM for general queries"""
        summary = self.engine.get_summary()
        
        prompt = f"""You are a data analyst assistant. The dataset contains:

Entities: {summary['entities']}
Relationships: {summary['relationships']}

User question: {query}

Provide a helpful response about what data is available, or explain how they could query it.
Keep response under 100 words."""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content
        except:
            return "The dataset contains billing documents, sales orders, deliveries, and products. Try asking about specific documents or flows."
