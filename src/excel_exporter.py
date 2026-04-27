"""
Excel Exporter Module - Export analysis results to Excel with charts
"""
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import LineChart, BarChart, Reference, StockChart
from openpyxl.chart.series import DataPoint
from datetime import datetime
from typing import Dict, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Class to export analysis to Excel"""
    
    @staticmethod
    def export_analysis(stocks_data: Dict, output_file: str = None):
        """
        Export stock analysis to Excel
        
        Args:
            stocks_data: Dictionary with analysis for multiple stocks
            output_file: Output file path (default: output/analysis_YYYYMMDD_HHMMSS.xlsx)
        """
        # Create output folder if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"stock_analysis_{timestamp}.xlsx"
        else:
            output_file = output_dir / output_file
        
        try:
            # Create Excel writer
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Write summary sheet
                ExcelExporter._write_summary_sheet(stocks_data, writer)
                
                # Write detailed analysis for each stock
                for stock_code, data in stocks_data.items():
                    ExcelExporter._write_stock_sheet(
                        stock_code, data, writer
                    )
            
            logger.info(f"Analysis exported to {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            return None
    
    @staticmethod
    def _write_summary_sheet(stocks_data: Dict, writer):
        """Write summary sheet"""
        summary_rows = []
        
        for stock_code, data in stocks_data.items():
            if 'analysis' in data and data['analysis']:
                analysis = data['analysis']
                signal, reason = data['signal'], data['reason']
                
                summary_rows.append({
                    '股票代號': stock_code,
                    '股票名稱': data.get('name', ''),
                    '今日收盤': analysis.get('close'),
                    'EMA12': analysis.get('ema_short'),
                    'EMA26': analysis.get('ema_long'),
                    'SMA20': analysis.get('sma_20'),
                    'BIAS%': analysis.get('bias'),
                    '訊號': signal,
                    '理由': reason
                })
        
        if summary_rows:
            df_summary = pd.DataFrame(summary_rows)
            df_summary.to_excel(writer, sheet_name='摘要', index=False)
            
            # Format summary sheet
            workbook = writer.book
            worksheet = writer.sheets['摘要']
            ExcelExporter._format_worksheet(worksheet)
    
    @staticmethod
    def _write_stock_sheet(stock_code: str, data: Dict, writer):
        """Write detailed sheet for a stock with charts at top"""
        if 'history' not in data or data['history'] is None:
            return
        
        df = data['history'].copy()
        
        # OHLC first (for StockChart), then indicators
        columns_to_export = [
            'Open', 'High', 'Low', 'Close',
            'EMA_Short', 'EMA_Long', 'SMA_20',
            'BIAS', 'MACD', 'Price_Change_Pct'
        ]
        
        available_columns = [col for col in columns_to_export if col in df.columns]
        df_export = df[available_columns].copy()
        
        # Rename columns to Chinese
        column_names = {
            'Open': '開盤價',
            'High': '最高價',
            'Low': '最低價',
            'Close': '收盤價',
            'EMA_Short': 'EMA12',
            'EMA_Long': 'EMA26',
            'SMA_20': 'SMA20',
            'BIAS': 'BIAS%',
            'MACD': 'MACD',
            'Price_Change_Pct': '漲跌%'
        }
        
        df_export = df_export.rename(columns=column_names)
        
        # Data starts at Excel row 36 to leave space for charts at top
        DATA_EXCEL_ROW = 36
        sheet_name = stock_code[:31]  # Excel sheet name max 31 chars
        df_export.to_excel(writer, sheet_name=sheet_name, index=True, startrow=DATA_EXCEL_ROW - 1)
        
        # Get worksheet and add charts at top
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Calculate data range for charts (header row + data rows)
        data_start_row = DATA_EXCEL_ROW        # Excel row of column headers
        data_end_row = data_start_row + len(df_export)
        
        # Format data area (pass real header row)
        ExcelExporter._format_worksheet(worksheet, header_row=data_start_row)
        
        # Add charts at top (before data)
        ExcelExporter._add_charts_at_top(worksheet, data_start_row, data_end_row, df_export)
    
    @staticmethod
    def _add_charts_at_top(worksheet, data_start_row: int, data_end_row: int, df_export):
        """Add charts at top of worksheet. Chart 1: price lines (Open/Close + EMA),
        Chart 2: BIAS%, Chart 3: MACD."""
        try:
            # Chart 1: LineChart – Open, Close, EMA12, EMA26, SMA20
            price_series = ['開盤價', '收盤價', 'EMA12', 'EMA26', 'SMA20']
            available_price = [c for c in price_series if c in df_export.columns]
            
            if available_price:
                chart1 = LineChart()
                chart1.title = "開盤/收盤 + 技術均線"
                chart1.style = 12
                chart1.height = 14
                chart1.width = 24
                chart1.y_axis.title = '股價'
                chart1.x_axis.title = '日期'
                chart1.grouping = "standard"
                chart1.smooth = False
                
                for col_name in available_price:
                    col_idx = df_export.columns.get_loc(col_name) + 2
                    ref = Reference(worksheet, min_col=col_idx,
                                    min_row=data_start_row, max_row=data_end_row)
                    chart1.add_data(ref, titles_from_data=True)
                
                worksheet.add_chart(chart1, "A1")
            
            # Chart 2: BIAS% (Bar Chart)
            if 'BIAS%' in df_export.columns:
                chart2 = BarChart()
                chart2.type = "col"
                chart2.title = "BIAS% (偏離率)"
                chart2.style = 11
                chart2.height = 8
                chart2.width = 20
                chart2.y_axis.title = 'BIAS%'
                
                bias_col = df_export.columns.get_loc('BIAS%') + 2
                data2 = Reference(worksheet, min_col=bias_col, min_row=data_start_row, max_row=data_end_row)
                chart2.add_data(data2, titles_from_data=True)
                
                worksheet.add_chart(chart2, "M1")
            
            # Chart 3: MACD (Bar Chart)
            if 'MACD' in df_export.columns:
                chart3 = BarChart()
                chart3.type = "col"
                chart3.title = "MACD 值"
                chart3.style = 10
                chart3.height = 8
                chart3.width = 20
                chart3.y_axis.title = 'MACD'
                
                macd_col = df_export.columns.get_loc('MACD') + 2
                data3 = Reference(worksheet, min_col=macd_col, min_row=data_start_row, max_row=data_end_row)
                chart3.add_data(data3, titles_from_data=True)
                
                worksheet.add_chart(chart3, "M12")
        
        except Exception as e:
            logger.warning(f"Could not add charts: {str(e)}")
    
    @staticmethod
    def _format_worksheet(worksheet, header_row: int = 1):
        """Apply formatting to worksheet. header_row is the 1-based Excel row of column headers."""
        header_fill = PatternFill(
            start_color="1F4E78",
            end_color="1F4E78",
            fill_type="solid"
        )
        header_font = Font(bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Format the actual header row
        for cell in worksheet[header_row]:
            if cell.value is not None:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Auto-adjust column widths based on data area only
        for column in worksheet.iter_cols(min_row=header_row, max_row=worksheet.max_row):
            max_length = 0
            col_letter = column[0].column_letter
            for cell in column:
                try:
                    if cell.value is not None:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
        
        # Add borders to data area only (header row onward)
        for row in worksheet.iter_rows(min_row=header_row, max_row=worksheet.max_row,
                                       min_col=1, max_col=worksheet.max_column):
            for cell in row:
                cell.border = thin_border
                if cell.row > header_row:
                    cell.alignment = Alignment(horizontal='right', vertical='center')
