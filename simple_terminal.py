import streamlit as st
import json
from datetime import datetime

def render_logs_simple(log_content: str):
    """
    Fallback simples: renderiza logs com markdown colorido
    """
    
    lines = log_content.split('\n')
    
    for line in lines:
        if not line.strip():
            continue
        
        try:
            # Tenta parsear como JSON
            data = json.loads(line)
            event = data.get('event', 'unknown')
            bot_id = data.get('bot_id', '-')
            timestamp = data.get('timestamp', 0)
            
            # Formata timestamp
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime('%H:%M:%S')
            
            # Cor baseada no evento
            if 'error' in event:
                icon = '🔴'
                color = 'red'
            elif 'trade' in event or 'executed' in event:
                icon = '🟢'
                color = 'green'
            elif 'target' in event:
                icon = '🟠'
                color = 'orange'
            elif 'order' in event:
                icon = '🟣'
                color = 'violet'
            elif 'price' in event:
                icon = '⚪'
                color = 'gray'
            else:
                icon = '🔵'
                color = 'blue'
            
            # Monta a linha
            parts = [
                f"`[{time_str}]`",
                f"**{bot_id}**",
                f"{icon} _{event.replace('_', ' ').title()}_"
            ]
            
            # Adiciona valores relevantes
            if 'price' in data:
                parts.append(f"**${data['price']:,.2f}**")
            
            if 'profit' in data:
                profit = data['profit']
                sign = '+' if profit > 0 else ''
                parts.append(f"💰 {sign}{profit:.2f}")
            
            if 'message' in data:
                parts.append(f"_{data['message']}_")
            
            # Renderiza
            st.markdown(' '.join(parts))
            
        except json.JSONDecodeError:
            # Não é JSON, mostra como texto
            st.text(line)
    
    st.divider()
