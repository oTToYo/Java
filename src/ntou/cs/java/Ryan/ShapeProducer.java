package ntou.cs.java.Ryan;

import java.awt.BorderLayout;
import java.awt.Container;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JTextField;
import javax.swing.UIManager;

public class ShapeProducer extends JFrame{
	
	PaintArea paintArea;
	JLabel info;
	public ShapeProducer()
	{
		Container con = getContentPane();
		UIManager.put("OptionPane.cancelButtonText", "Cancel");
	    UIManager.put("OptionPane.okButtonText", "OK");
	    int Num=0;
		String  NumText= JOptionPane.showInputDialog(
			    this,
			    "Number of shapes:",
			    "Input",
			    JOptionPane.QUESTION_MESSAGE
			    );
		try//檢查格式是否錯誤
		{
			Num=Integer.parseInt(NumText);
		}
		catch(NumberFormatException e)//格式錯誤例外
		{
			JOptionPane.showMessageDialog(this,
				    "Enter wrong format",
				    "Format error",
				    JOptionPane.ERROR_MESSAGE);
			 System.exit(0);
		}
		addWindowListener(new WindowAdapter(){//設定關閉視窗及關閉程式
			public void windowClosing(WindowEvent e) {
		        System.exit(0);
		    }
			
		});
		
		info = new JLabel("");
		paintArea = new PaintArea(Num,info);
		
		con.add(BorderLayout.CENTER,paintArea);
		con.add(BorderLayout.SOUTH,info);
		paintArea.repaint();
		setVisible(true);
		setSize(800,500);
	}
	public static void main(String []args)
	{
		ShapeProducer Producer = new ShapeProducer();
	}
}
