package ntou.cs.java.Ryan;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Point;

import javax.swing.JComponent;

public abstract class MyShape{
	private Color color;
	private int x,y;
	public MyShape()
	{
		x=0;
		y=0;
		color = Color.BLACK;
	}
	public MyShape(int x,int y,Color color)
	{
		this.x=x;
		this.y=y;
		this.color = color;
	}
	public void setX(int x)
	{
		this.x= x;
	}
	public void setY(int y)
	{
		this.y= y;
	}
	public void setColor(Color color)
	{
		this.color= color;
	}
	public int getX()
	{
		return x;
	}
	public int getY()
	{
		return y;
	}
	
	public Color getColor()
	{
		return color;
	}
	public boolean containsPoint(Point p)
	{
		return false;
	}
	public abstract void draw(Graphics g);
}

 class MyLine extends MyShape {
	 private int endX,endY;
	 public MyLine()
	 {
		 endX=0;
		 endY=0;
	 }
	 public MyLine(int x,int y,int endX,int endY,Color color)
		{
			setX(x);
			setX(y);
			setColor(color);
			this.endX=endX;
			this.endY=endY;
		}
	@Override
	public void draw(Graphics g) {
		
		g.setColor(getColor());
		g.drawLine(0,0,endX,endY);
	}

}
 
 class MyOval extends MyShape {
	 boolean filled;
	 private int width,height;
	 public MyOval()
	 {
		 filled = false;
		 width = 100;
		 height = 100;
	 }
	 public MyOval(int x,int y,int width,int height,Color color,boolean filled)
	 {
		this.filled = filled;
		setX(x);
		setY(y);
		setColor(color);
		this.width = width;
		this.height = height;
	 }
		@Override
		public void draw(Graphics g) {
			
			g.setColor(getColor());
			if(filled)
				g.fillOval(getX(), getY(), width,height);
			else
				g.drawOval(getX(), getY(), width, height);	
		}
		@Override
		public boolean containsPoint(Point p)
		{
			if(filled)
			{
				if((getX()<=p.x&&getX()+width>=p.x )&&(getY()<=p.y&&getY()+height>=p.y))
				return true;
			}
			return false;
		}

	}
 class MyRect extends MyShape {
	 boolean filled;
	 private int width,height;
	 Graphics grahpic;
	 public MyRect()
	 {
		 filled = false;
		 width = 100;
		 height = 100;
	 }
	 public MyRect(int x,int y,int width,int height,Color color,boolean filled)
		{
		    this.filled = filled;
			setX(x);
			setY(y);
			setColor(color);
			this.width = width;
			this.height = height;
		}
		@Override
		public void draw(Graphics g) {
			grahpic = g;
			g.setColor(getColor());
			if(filled)
				g.fillRect(getX(), getY(), width, height);
			else
				g.drawRect(getX(), getY(), width, height);
			
		}
		@Override
		public boolean containsPoint(Point p)
		{
			if(filled)
			{
				if((getX()<=p.x&&getX()+width>=p.x )&&(getY()<=p.y&&getY()+height>=p.y))
				return true;
			}
			return false;
		}

	}


