package ntou.cs.java.Ryan;

import java.awt.Color;
import java.awt.Container;
import java.awt.Graphics;
import java.awt.Point;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.MouseMotionAdapter;


import javax.swing.JLabel;
import javax.swing.JPanel;

public class PaintArea extends JPanel{
	int shapeNum;
	MyShape shapes[];
	JLabel info;
	Point p;
	 int moveX,moveY,rectIndex;
	public PaintArea(int shapeNum,JLabel info)
	{
		this.shapeNum = shapeNum;
		this.info = info;
		shapes = new MyShape[shapeNum];
		setBackground(Color.white);
		this.addMouseListener(new MouseProcess());
		this.addMouseMotionListener(new MouseMotionProcess());
		creatShapes();
	}
	private void creatShapes()
	{
		int lineCount=0,ovalCount=0,rectCount=0;
		for(int i=0;i<shapeNum;i++)
		{
			int type = (int)(Math.random()*3);
			int xPosition = (int)(Math.random()*400);
			int yPosition = (int)(Math.random()*160);
			int fill = (int)(Math.random()*2);
			int R= (int)(Math.random()*256);
			int G= (int)(Math.random()*256);
			int B= (int)Math.random()*256;
			//System.out.println(xPosition+"_"+yPosition);
			switch(type)
			{
			case 0:lineCount++;
				shapes[i] = new MyLine(xPosition,yPosition,xPosition*type,xPosition-type*5,new Color(R,G,B));
			break;
			case 1:ovalCount++;
				shapes[i] = new MyOval(xPosition,yPosition,xPosition*type,yPosition*type,new Color(R,G,B),(fill==0)?false:true);
			break;
			case 2:rectCount++;
				shapes[i] = new MyRect(xPosition,yPosition,xPosition*type,yPosition*type,new Color(R,G,B),(fill==0)?false:true);
			break;
			default:
				
			}
		}
		
		info.setText("Lines:"+lineCount+",Ovals:"+ovalCount+",Rectangles:"+rectCount);
	}
	public void paintComponent(Graphics g)
	{
		super.paintComponent(g);
		for(int i=0;i<shapeNum;i++)
		{
			shapes[i].draw(g);
	    }
	}
		private class MouseProcess extends MouseAdapter  
	    {  
	        public void mouseClicked(MouseEvent e)  
	        { 
	        
	        	 
	        }  
	        public void  mousePressed(MouseEvent e)  
	        {  
	        	Point p= e.getPoint();
	        	rectIndex = getRect(p);
	        	System.out.println(rectIndex);
	        	if(rectIndex>=0)
	        	{
	        	moveX = p.x-shapes[rectIndex].getX();
	        	moveY= p.y-shapes[rectIndex].getY();
	        	}
	        } 
	    }
	 private class MouseMotionProcess extends MouseMotionAdapter  
	    {
	       public void mouseDragged(MouseEvent e)  
	       {  
	           Point p= e.getPoint();
	            
	          if(rectIndex>=0)
	          {
	        	  shapes[rectIndex].setX(p.x-moveX);
	        	  shapes[rectIndex].setY(p.y-moveY);
	          }
	          repaint();
	        }  
	  }
		
	 private int getRect(Point p)
	 {
		 for(int i=0;i<shapeNum;i++)
		 {
			 //System.out.print(shapes[i].containsPoint(p));
			 if(shapes[i].containsPoint(p))
			 return i;
		 }
		return -1;
	 }
		
	
}
