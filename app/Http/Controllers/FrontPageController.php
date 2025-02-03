<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class FrontPageController extends Controller
{
    public function index()
    {
        // Simply return the frontpage view
        return view('frontpage');
    }
}
