package ntou.cs.java.Ryan;
import java.awt.BorderLayout;
import java.awt.Font;
import java.awt.GridLayout;
import java.math.BigDecimal;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;


import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTextField;

public class Calculator extends JFrame{
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private JPanel jp;//中間放置運算按鈕的區塊
	private JButton digitBtn[];//放置數字的Button陣列
	private JButton opBtn[];//放置運算的Button陣列
	private String op[] = {"=","+","-","*","C",".","/"};
	private JTextField jt ;//取得使用者輸入
	private static final int digitBtnNum = 10;//數字個數
	private static final int opBtnNum = 7;// operator個數
	private int lastOp;
	private double lastNum;
	private boolean checkOp;
	public Calculator(String title)
	{
		super(title);
		
		jp = new JPanel();//Instance JPanle原件
		
		digitBtn = new JButton[digitBtnNum];//初始化digitButton
		for(int i=0;i<digitBtnNum;i++)
		{
			digitBtn[i]= new JButton(Integer.toString(i));
			digitBtn[i].addActionListener(new DigitListener());
			digitBtn[i].setFont(new Font("serif",0,22));
		}
		opBtn = new JButton[opBtnNum];//初始opButton
		for(int i=0;i<opBtnNum;i++)
		{
			opBtn[i]= new JButton(op[i]);
			opBtn[i].addActionListener(new opListener());
			opBtn[i].setFont(new Font("serif",0,22));
		}
		lastOp=-1;//初始化目前沒有指令
		lastNum=0;//初始化目前沒有值
		checkOp = false;
		jt = new JTextField();
		jt.setHorizontalAlignment(JTextField.RIGHT);
		jt.setText("0");
		jt.setFont(new Font("serif",0,22));
		
		//jt.setSize(230, 50);
		
		setResizable(false);
		setSize(227, 286);
		setVisible(true);
		addWindowListener(new WindowAdapter(){//設定關閉視窗及關閉程式
			public void windowClosing(WindowEvent e) {
		        System.exit(0);
		    }
		});
		init();
		
	}
	
	public void init()
	{
		JPanel con = new JPanel();
		con.setBorder(BorderFactory.createEmptyBorder(7, 7, 7, 7));
		con.setLayout(new BorderLayout());
		
		GridLayout leftLayout= new GridLayout(4,3);
		leftLayout.setHgap(2);
		leftLayout.setVgap(2);
		
		GridLayout rightLayout= new GridLayout(4,1);
		rightLayout.setHgap(2);
		rightLayout.setVgap(2);
		
		JPanel leftPan = new JPanel();
		leftPan.setLayout(leftLayout);//設定中間放置按鈕為GridLayout
		JPanel rightPan = new JPanel();
		rightPan.setLayout(rightLayout);
		for(int i=digitBtnNum-3;i>0;i-=3)
		{
			leftPan.add(digitBtn[i]);
			leftPan.add(digitBtn[i+1]);
			leftPan.add(digitBtn[i+2]);
		}
		
		leftPan.add(opBtn[4]);
		leftPan.add(digitBtn[0]);
		leftPan.add(opBtn[5]);
		leftPan.add(opBtn[6]);
		
		rightPan.add(opBtn[1]);
		rightPan.add(opBtn[2]);
		rightPan.add(opBtn[3]);
		rightPan.add(opBtn[6]);
		
		
		jp.add(leftPan);
		jp.add(rightPan);
		
		con.add(BorderLayout.NORTH,jt);//將輸入欄位放到北邊
		con.add(BorderLayout.CENTER,jp);//將Button放在中間
		con.add(BorderLayout.SOUTH,opBtn[0]);//將'='放在南邊
		
		getContentPane().add(con);
		
		
	}
	
	class DigitListener implements ActionListener
	{
		@Override
		public void actionPerformed(ActionEvent e) 
		{
			for(int i=0;i<digitBtnNum;i++)
			{
				if(e.getSource()==digitBtn[i])
				{
					String currentText = jt.getText();
					
					if(checkOp)
					{
						jt.setText(Integer.toString(i));
						checkOp = false;
					}
					else
					{
						System.out.println("!:"+Integer.toString(i));
						if(!currentText.endsWith(".")&&(Double.parseDouble(currentText)==0||lastOp==0))
						{
							
							System.out.println("?");
							currentText="";
							lastOp=-1;
							
						}
						System.out.println("");
						jt.setText(currentText+Integer.toString(i));	
					}
					break;
				}
			}
		}
	}
	class opListener implements ActionListener
	{
		@Override
		public void actionPerformed(ActionEvent e) 
		{
			if(e.getSource()==opBtn[0])//定義Assign
				opSwitcher(0);
			else if(e.getSource()==opBtn[1])//定義Plus
				opSwitcher(1);
			else if(e.getSource()==opBtn[2])//定義Minus
				opSwitcher(2);
			else if(e.getSource()==opBtn[3])//定義multiply
				opSwitcher(3);
			else if(e.getSource()==opBtn[4])//定義Clear
				opSwitcher(4);
			else if(e.getSource()==opBtn[5])//定義Dot
				opSwitcher(5);
			else//定義division
				opSwitcher(6);
		}
	}
	private void opSwitcher(int op)
	{
		
		String currentText = jt.getText();
		Double currentNum = Double.valueOf(currentText);
		System.out.println("current:"+currentNum);
		if(op==4)//clear
		{
			jt.setText("0");
			checkOp=false;
			lastNum=0;
			lastOp=-1;
			lastOp = op;
		}
		else if(op==5)//dot
		{
			
			System.out.println(String.valueOf(currentNum));
			if(lastOp!=op&&String.valueOf(currentNum).endsWith(".0"))
			{
				jt.setText(currentText+".");
				System.out.println("yes");
			}
			
		}
		else 
		{
			if(checkOp)
				lastOp = op;
			else
			{
			switch(lastOp)
			{
			case 1://plus
				lastNum=add(lastNum,currentNum);
				System.out.println(lastNum);
				break;
			case 2://minus
				lastNum=sub(lastNum,currentNum);
				break;
			case 3://multiply
				lastNum=mul(lastNum,currentNum);
				break;
			case 6://divide
				lastNum=div(lastNum,currentNum,10);
				break;
			default:
				lastNum = currentNum;
				System.out.println("defaule:"+lastNum);
			}
			checkOp=true;
			if(String.valueOf(lastNum).endsWith(".0"))
			jt.setText(String.valueOf((int)lastNum));
			else
			jt.setText(String.valueOf(lastNum));
			lastOp = op;
		}
		}
		if(op==0)
		{
			checkOp=false;
			if(String.valueOf(lastNum).endsWith(".0"))
				jt.setText(String.valueOf((int)lastNum));
				else
				jt.setText(String.valueOf(lastNum));
			lastOp = op;
		}
		
	}
	private static double add(double v1,double v2) {
		    BigDecimal b1 = new BigDecimal(Double.toString(v1));
		    BigDecimal b2 = new BigDecimal(Double.toString(v2));
		    return b1.add(b2).doubleValue();
		}
	private static double sub(double v1,double v2) {
		    BigDecimal b1 = new BigDecimal(Double.toString(v1));
		    BigDecimal b2 = new BigDecimal(Double.toString(v2));
		    return b1.subtract(b2).doubleValue();
		}
	private static double mul(double v1,double v2) {
		    BigDecimal b1 = new BigDecimal(Double.toString(v1));
		    BigDecimal b2 = new BigDecimal(Double.toString(v2));
		    return b1.multiply(b2).doubleValue();
		}
	private static double div(double v1,double v2,int scale) {
			if(v2==0)
			return 0.0;
		     if (scale < 0) {
		        throw new IllegalArgumentException(
		        "The scale must be a positive integer or zero");
		     }
		     BigDecimal b1 = new BigDecimal(Double.toString(v1));
		     BigDecimal b2 = new BigDecimal(Double.toString(v2));
		     return b1.divide(b2,scale,BigDecimal.ROUND_HALF_UP).doubleValue();
		 }
	
	public static void main(String []args)
	{
		Calculator cal = new Calculator("NTOU Calculator");
	}
}
